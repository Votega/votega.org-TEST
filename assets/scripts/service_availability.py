from zeep import Client
wsdl = "http://webservices.legis.ga.gov/Legislation/Service.svc?wsdl"
client = Client(wsdl)

print("\nOperations the service actually offers:")
for name in sorted(client.service._binding._operations):
    print(" •", name)