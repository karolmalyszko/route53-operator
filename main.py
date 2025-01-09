import boto3
import json, requests, logging

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%d-%m-%Y %H:%M",
    level=logging.DEBUG,
    # level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = boto3.client('route53')

domainName = 'jaskiniaops.com'
# subdomainList = ['photos', 'nxt']
subdomainList = ['test']

def getRecordValue( subdomain ):
    logger.debug("Getting DNS record value.")
    status = False
    try:
        rsp = client.list_resource_record_sets(
            HostedZoneId=hostedZoneID,
            StartRecordName="{}.{}".format(subdomain, domainName),
            StartRecordType='A',
            MaxItems='1'
        )
        status = True
    except:
        logger.error("Failed getting DNS record value for {}".format(subdomain))

    if status:
        logger.debug("DNS record value retrieved")
        return True, json.dumps(rsp["ResourceRecordSets"][0]["ResourceRecords"][0]["Value"]).strip("\"")
    else:
        return False, None

def getHostedZoneID( zoneName ):
    logger.debug("Getting hosted DNS zone ID for further operations")
    status = False
    try:
        rsp = client.list_hosted_zones_by_name(
            DNSName=zoneName,
            MaxItems='1'
        )
        status = True
    except:
        logger.error("Invalid domain name provided")

    if status:
        logger.debug("Hosted zone ID retrieved.")
        return True, json.dumps(rsp["HostedZones"][0]["Id"]).split("/", 2)[2].strip("\"")
    else:
        return False, None

def updateRecordValue( subdomain, newIp ):
    logger.info("Changing '{}' record to {}".format(subdomain, newIp))
    status = False
    try:
        rsp = client.change_resource_record_sets(
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': '{}.{}'.format(subdomain, domainName),
                            'ResourceRecords': [
                                {
                                    'Value': '{}'.format(newIp),
                                },
                            ],
                            'TTL': 60,
                            'Type': 'A',
                        },
                    },
                ]
            },
            HostedZoneId=hostedZoneID,
        )
        changeId = json.dumps(rsp["ChangeInfo"]["Id"]).strip("\"")
        changeStatus = json.dumps(rsp["ChangeInfo"]["Status"]).strip("\"")
    except:
        logger.error("Changing DNS record for {} failed!".format(subdomain))

    if status:
        logger.debug("DNS record for {} updated".format(subdomain))
        return True, changeId, changeStatus
    else:
        return False, None, None

def getCurrentIP():
    logging.debug("Getting current IP address from ifconfig.me")
    status = False
    try:
        ip = requests.get('https://ifconfig.me').text
        status = True
    except:
        logger.error("Something went wrong calling ifconfig.me")

    if status:
        logger.debug("Current IP retrieved")
        return True, ip
    else:
        return False, None

#======== start of script execution
status, id = getHostedZoneID(domainName)
if status:
    hostedZoneID = id

status, ip = getCurrentIP()
if status:
    currentIp = ip

for subdomain in subdomainList:
    logger.debug("Checking for differences")
    status, remoteIp = getRecordValue(subdomain)
    if status:
        if remoteIp != currentIp:
            logger.info("Changes found for '{}' subdomain".format(subdomain))
            changeID, changeStatus = updateRecordValue(subdomain, currentIp)
        else: logger.info("No changes for '{}' subdomain found".format(subdomain))
    # status.append(partial)

# photosIp = getRecordValue( "photos" )
# status = ["photos", photosIp]
# print(status)

# for entity in status:
#     if entity[2] != entity[1]:
#         print("changing {} ip entry from {} to {}".format(entity[0], entity[1], entity[2]))
#     else:
#         print("No changes required for {} subdomain".format(entity[0]))

# id, status = updateRecordValue( "test", currentIp )
# # if status != "PENDING" || status != "INSYNC" :
# #     print("error")
# # else:
# response = client.get_change(Id=id)
# # print(json.dumps(response, indent=4))
# print(response)

# # TODO
# dodać powiadamianie mailowe za pomocą AWS SES
# nazwa domeny podawana jako zmienna środowiskowa / z poziomu pliku konfiguracyjnego
# subdomeny podawane jako zmienne środowiskowe / z poziomu pliku konfiguracyjnego
