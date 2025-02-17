import boto3
import json, requests, logging, os
from botocore.exceptions import ClientError

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%d-%m-%Y %H:%M",
    level=os.environ.get("LOGLEVEL", "INFO")
)
logger = logging.getLogger(__name__)

client = boto3.client('route53')

domainName = os.environ.get("DOMAIN_NAME")
subdomainList = os.environ.get("SUBDOMAINS").split(",")

def getRecordValue( subdomain, hostedZoneID ):
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

def updateRecordValue( subdomain, newIp, hostedZoneID ):
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
        status = True
    except:
        logger.error("Changing DNS record for '{}' failed!".format(subdomain))

    if status:
        logger.debug("DNS record for '{}' updated".format(subdomain))
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

def emailNotify():
    sender = "Automated notifier <noreply@jaskiniaops.com>"
    recipient = "karol.malyszko@gmail.com"
    awsRegion = "us-east-1"
    subject = "Automated notification for dnsOperator job"
    charset = "UTF-8"
    bodyText = "Notification : dnsOperator has found and successfully updated new public IP address for tools running in Sukienna. All should be good in a little while."
    bodyHtml = """<html>
<head></head>
<body>
  <h1>dnsOperator has done it's job.</h1>
  <p>
    <b>dnsOperator</b> has found and successfully updated new public IP address for tools running in Sukienna. All should be good in a little while.
  </p>
</body>
</html>
            """

    sesClient = boto3.client('ses',region_name=awsRegion)

    try:
        #Provide the contents of the email.
        response = sesClient.send_email(
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': charset,
                        'Data': bodyHtml,
                    },
                    'Text': {
                        'Charset': charset,
                        'Data': bodyText,
                    },
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=sender,
        )
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        exit(5)
    else:
        logger.info("Email notification sent!"),
        logger.debug(response['MessageId'])

def main():
    status, id = getHostedZoneID(domainName)
    if status:
        hostedZoneID = id
    else:
        logger.error("Getting hosted zone id failed. Exiting")
        exit(1)

    status, ip = getCurrentIP()
    if status:
        currentIp = ip
    else:
        logger.error("Getting current ip failed. Exiting")
        exit(2)

    for subdomain in subdomainList:
        logger.debug("Checking for differences")
        status, remoteIp = getRecordValue(subdomain, hostedZoneID)
        if status:
            if remoteIp != currentIp:
                logger.info("Changes found for '{}' subdomain".format(subdomain))
                status, changeID, changeStatus = updateRecordValue(subdomain, currentIp, hostedZoneID)
                if not status:
                    logger.error("Updating DNS record failed. Exiting")
                    exit(3)
                else:
                    emailNotify()
            else: logger.info("No changes for '{}' subdomain found".format(subdomain))
        else:
            logger.error("Something went wrong retrieving current record value. Exiting")
            exit(4)

if __name__ == '__main__':
    main()
