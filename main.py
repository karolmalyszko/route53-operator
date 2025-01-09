import boto3
import json, requests

client = boto3.client('route53')

domainName = 'jaskiniaops.com'
subdomainList = ['photos', 'nxt']

def getRecordValue( subdomain ):
    rsp = client.list_resource_record_sets(
        HostedZoneId=hostedZoneID,
        StartRecordName="{}.{}".format(subdomain, domainName),
        StartRecordType='A',
        MaxItems='1'
    )

    return json.dumps(rsp["ResourceRecordSets"][0]["ResourceRecords"][0]["Value"]).strip("\"")
    # print(json.dumps(rsp["ResourceRecordSets"], indent=4))
    # print(ip)

def getHostedZoneID( zoneName ):
    rsp = client.list_hosted_zones_by_name(
        DNSName=zoneName,
        MaxItems='1'
    )

    return json.dumps(rsp["HostedZones"][0]["Id"]).split("/", 2)[2].strip("\"")

def updateRecordValue( subdomain, newIp ):
    # print("Modding {} record to {}".format(subdomain, newIp))
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

    return changeId, changeStatus

hostedZoneID = getHostedZoneID( domainName )
currentIp = requests.get('https://ifconfig.me').text

for subdomain in subdomainList:
    remoteIp = getRecordValue( subdomain )
    if remoteIp != currentIp:
        print("Changing {} ip entry from {} to {}".format(subdomain, remoteIp, currentIp))
        id, status = updateRecordValue(subdomain, currentIp)
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
# dodać łowienie exceptions przy wywołaniach funkcji zarządzających Route53
# dodać logowanie
#     - do konsoli
#     - do pliku
# dodać powiadamianie mailowe za pomocą AWS SES
# nazwa domeny podawana jako zmienna środowiskowa / z poziomu pliku konfiguracyjnego
# subdomeny podawane jako zmienne środowiskowe / z poziomu pliku konfiguracyjnego
