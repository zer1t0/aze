import argparse
import dns.resolver
import dns
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import sys
import logging
from . import read_in

logger = logging.getLogger("aze")

SERVICE_DOMAIN_NAMES =  {
    'onmicrosoft.com': 'Microsoft Hosted Domain',
	'scm.azurewebsites.net': 'App Services - Management',
	'azurewebsites.net': 'App Services',
	'p.azurewebsites.net': 'App Services',
	'cloudapp.net': 'App Services',
	'file.core.windows.net': 'Storage Accounts - Files',
	'blob.core.windows.net': 'Storage Accounts - Blobs',
	'queue.core.windows.net': 'Storage Accounts - Queues',
	'table.core.windows.net': 'Storage Accounts - Tables',
	'mail.protection.outlook.com': 'Email',
	'sharepoint.com': 'SharePoint',
	'redis.cache.windows.net': 'Databases-Redis',
	'documents.azure.com': 'Databases-Cosmos DB',
	'database.windows.net': 'Databases-MSSQL',
	'vault.azure.net': 'Key Vaults',
	'azureedge.net': 'CDN',
	'search.windows.net': 'Search Appliance',
	'azure-api.net': 'API Services',
	'azurecr.io': 'Azure Container Registry',
}


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
        "--workers",
        "-w",
        default=10,
        type=int,
        help="Number of concurrent workers"
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
        "--verbose",
        "-v",
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

    service_domains = list(SERVICE_DOMAIN_NAMES.keys())

    try:
        for subdomain in read_in.read_text_targets(args.subdomains):
            for service_domain in service_domains:
                pool.submit(
                    dns_resolution,
                    subdomain,
                    service_domain,
                    resolver,
                    tcp,
                    print_lock,
                )
    except (KeyboardInterrupt, BrokenPipeError):
        pass

def dns_resolution(subdomain, service_domain, resolver, tcp, print_lock):
    domain = subdomain + "." + service_domain
    found = False
    try:
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
        level = logging.INFO
    elif verbosity > 1:
        level = logging.DEBUG
    else:
        level = logging.WARN

    logging.basicConfig(
        level=level,
        filename=log_file,
        format="%(levelname)s:%(name)s:%(message)s"
    )


