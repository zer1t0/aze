import argparse
import requests
from xml.etree import ElementTree
from .error import AzeError
from . import read_in

def parse_args():
    parser = argparse.ArgumentParser(
        description="Discover the domains associated with a tenant",
    )
    parser.add_argument(
        "domain",
        nargs="*",
        help="An Azure tenant domain. If none then stdin is used."
    )
    return parser.parse_args()

def main():
    args = parse_args()

    try:
        for domain in read_in.read_text_targets(args.domain):
            for d in request_tenant_domains(domain):
                print(d)
    except KeyboardInterrupt:
        pass


def request_tenant_domains(domain):
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": 'http://schemas.microsoft.com/exchange/2010/Autodiscover/Autodiscover/GetFederationInformation',
        "User-Agent": "AutodiscoverClient"
    }

    body = """
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:exm="http://schemas.microsoft.com/exchange/services/2006/messages" xmlns:ext="http://schemas.microsoft.com/exchange/services/2006/types" xmlns:a="http://www.w3.org/2005/08/addressing" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
	<soap:Header>
		<a:Action soap:mustUnderstand="1">http://schemas.microsoft.com/exchange/2010/Autodiscover/Autodiscover/GetFederationInformation</a:Action>
		<a:To soap:mustUnderstand="1">https://autodiscover-s.outlook.com/autodiscover/autodiscover.svc</a:To>
		<a:ReplyTo>
			<a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address>
		</a:ReplyTo>
	</soap:Header>
	<soap:Body>
		<GetFederationInformationRequestMessage xmlns="http://schemas.microsoft.com/exchange/2010/Autodiscover">
			<Request>
				<Domain>{}</Domain>
			</Request>
		</GetFederationInformationRequestMessage>
	</soap:Body>
</soap:Envelope>
""".format(domain)

    resp = requests.post(
        "https://autodiscover-s.outlook.com/autodiscover/autodiscover.svc",
        headers=headers,
        data=body.strip(),
    )
    if resp.status_code != 200:
        raise AzeError(
            "Error in HTTP request retrieving domains: {}".format(
                resp.status_code
            ))

    return extract_domains_from_resp(resp.text)


def extract_domains_from_resp(text):
    root = ElementTree.fromstring(text)
    ns = {
        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
        "": "http://schemas.microsoft.com/exchange/2010/Autodiscover"
    }
    domains = [
        d.text
        for d in root.findall(
                "./soap:Body/GetFederationInformationResponseMessage/Response/Domains/Domain",
                ns
        )
    ]
    return domains
