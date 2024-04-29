import argparse
import dns.resolver
import dns
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import sys
import logging
from . import read_in
from .permutations import DEFAULT_PERMUTATIONS

logger = logging.getLogger("aze")

SERVICE_DOMAIN_NAMES =  {
    "onmicrosoft.com": "Microsoft Hosted Domain",
	"scm.azurewebsites.net": "App Services - Management",
	"azurewebsites.net": "App Services",
	"p.azurewebsites.net": "App Services",
	"cloudapp.net": "App Services",
	"file.core.windows.net": "Storage Accounts - Files",
	"blob.core.windows.net": "Storage Accounts - Blobs",
	"queue.core.windows.net": "Storage Accounts - Queues",
	"table.core.windows.net": "Storage Accounts - Tables",
	"mail.protection.outlook.com": "Email",
	"sharepoint.com": "SharePoint",
	"redis.cache.windows.net": "Databases-Redis",
	"documents.azure.com": "Databases-Cosmos DB",
	"database.windows.net": "Databases-MSSQL",
	"vault.azure.net": "Key Vaults",
	"azureedge.net": "CDN",
	"search.windows.net": "Search Appliance",
	"azure-api.net": "API Services",
	"azurecr.io": "Azure Container Registry",
    "azuredatalakestore.net": "Azure Data Lake",
}

SERVICE_KEYWORDS =  {
    "domain": ["onmicrosoft.com"],
    "app": [
        "scm.azurewebsites.net",
        "azurewebsites.net",
        "p.azurewebsites.net",
        "cloudapp.net",
    ],
	"file": ["file.core.windows.net"],
    "blob": ["blob.core.windows.net"],
	"queue": ["queue.core.windows.net"],
    "table": ["table.core.windows.net"],
    "lake": ["azuredatalakestore.net"],
    "storage": [
        "file.core.windows.net",
        "blob.core.windows.net",
        "queue.core.windows.net",
        "table.core.windows.net",
        "azuredatalakestore.net"
    ],
    "email": ["mail.protection.outlook.com"],
    "mail": ["mail.protection.outlook.com"],
    "sharepoint": ["sharepoint.com"],
	"redis": ["redis.cache.windows.net"],
    "cosmos": ["documents.azure.com"],
    "mssql": ["database.windows.net"],
    "db": [
        "redis.cache.windows.net",
        "documents.azure.com",
        "database.windows.net"
    ],
    "vault": ["vault.azure.net"],
	"cdn": ["azureedge.net"],
	"search": ["search.windows.net"],
	"api": ["azure-api.net"],
	"container": ["azurecr.io"],
	"registry": ["azurecr.io"],
}

DEFAULT_WORKERS = 2

def parse_args():
    parser = argparse.ArgumentParser(
        description="Check if any Azure service is using the given subdomains.",
    )
    parser.add_argument(
        "subdomains",
        nargs="*",
        help="Specify several subdomains or files. If None then stdin is used"
    )

    parser.add_argument(
        "-w", "--workers",
        default=DEFAULT_WORKERS,
        type=int,
        help="Number of concurrent workers. Default: {}".format(DEFAULT_WORKERS)
    )

    parser.add_argument(
        "-p", "--permutations",
        nargs="*",
        help="Words or file with words per line to create permutations of subdomains."
    )

    parser.add_argument(
        "--no-permutations",
        action="store_true",
        help="Do not use the default permutations.",
    )

    parser.add_argument(
        "-s", "--service",
        help="Indicate the services to bruteforce subdomains. If none is specified, then all will be used.",
        nargs="*",
        choices=list(SERVICE_KEYWORDS.keys()),
    )

    parser.add_argument(
        "--tcp",
        action="store_true",
        default=False,
        help="Use TCP"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=5000,
        help="Timeout milliseconds, default 5000"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="Verbosity",
        default=0
    )

    args = parser.parse_args()
    args.timeout = args.timeout / 1000

    return args

def main():
    args = parse_args()
    init_log(args.verbose)

    pool = ThreadPoolExecutor(args.workers)
    print_lock = Lock()

    resolver = dns.resolver.Resolver()
    resolver.timeout = args.timeout
    tcp=args.tcp

    if args.permutations:
        permutations = list(read_in.read_text_targets(
            args.permutations,
            use_stdin_if_none=False,
            use_stdin_if_minus=False,
        ))
    elif args.no_permutations:
        permutations = []
    else:
        permutations = DEFAULT_PERMUTATIONS

    if args.service:
        service_domains = set()
        for service_keyword in args.service:
            service_domains.update(SERVICE_KEYWORDS[service_keyword])
    else:
        service_domains = set(SERVICE_DOMAIN_NAMES.keys())

    try:
        for subdomain in read_in.read_text_targets(args.subdomains):
            for service_domain in service_domains:
                for subdomain_perm in apply_permutations(
                        subdomain, permutations
                ):
                    pool.submit(
                        dns_resolution,
                        subdomain_perm,
                        service_domain,
                        resolver,
                        tcp,
                        print_lock,
                    )
    except (KeyboardInterrupt, BrokenPipeError):
        pass

def apply_permutations(base, permutations):
    yield base
    for word in permutations:
        yield word + "-" + base
        yield base + "-" + word
        yield word + base
        yield base + word

def dns_resolution(subdomain, service_domain, resolver, tcp, print_lock):
    domain = subdomain + "." + service_domain
    found = False
    try:
        logging.info("Checking {}".format(domain))
        resolve_record("SOA", domain, resolver, tcp)
        found = True
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoAnswer:
        # This means that there is no specific answer for the SOA query
        # but there is an answer so we are good.
        found = True
        pass
    except Exception as ex:
        logger.warning(
            "Error %s resolving '%s': %s",
            type(ex).__name__, domain, ex
        )
        raise ex

    if found:
        with print_lock:
            logger.info("Service '{}' domain found: {}".format(
                SERVICE_DOMAIN_NAMES[service_domain],
                domain
            ))
            print(domain)

def resolve_record(q_type, host, resolver, tcp):
    logger.debug("Resolving '%s' records %s", q_type, host)
    results = resolver.resolve(host, q_type, tcp=tcp)
    return [str(d) for d in results]


def init_log(verbosity=0, log_file=None):

    if verbosity == 1:
        level = logging.WARN
    elif verbosity == 2:
        level = logging.INFO
    elif verbosity > 2:
        level = logging.DEBUG
    else:
        level = logging.ERROR

    logging.basicConfig(
        level=level,
        filename=log_file,
        format="%(levelname)s:%(name)s:%(message)s"
    )


