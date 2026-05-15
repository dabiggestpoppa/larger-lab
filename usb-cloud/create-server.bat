@echo off
echo Creating Kamatera server...
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\cloudcli.exe server create --name larger-lab-agent --datacenter US-NY2 --image "Ubuntu 24.04" --cpu 2B --ram 4096 --disk id=0,size=50 --network id=0,name=wan,ip=auto --password "TempPass123!" --api-clientid 84908b7a4714aacd25c51715e0efe96e --api-secret 9cd519e13f62ef5522736cb103328ba8 --wait
echo.
echo Server creation complete.
echo.
echo Listing servers:
c:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\cloudcli.exe server list --api-clientid 84908b7a4714aacd25c51715e0efe96e --api-secret 9cd519e13f62ef5522736cb103328ba8