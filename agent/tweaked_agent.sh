#!/bin/sh
export DEBIAN_FRONTEND=noninteractive

cd ~/wptagent

location=`curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/location" -H "Metadata-Flavor: Google"`
echo "Loaded location: $location"

torMode=false
withTimer="tor-with-timer"
withoutTimer="tor-without-timer"
torLocation=""
torStateLocal=""
stateLocation="/Browser/TorBrowser/Data/Tor/state"
torArg="--torbrowser"
if printf -- '%s' "$location" | egrep -q -- "$withTimer"
then 
	torMode=true
	echo "Engage timer mode"
	torLocation="../with-timer-changes/tor-browser_en-US"
        torStateLocal="$torLocation$stateLocation"
elif printf -- '%s' "$location" | egrep -q -- "$withoutTimer"
then 
	torMode=true
	echo "No Timer Mode"
	torLocation="../without-timer-change/tor-browser_en-US" 
        torStateLocal="$torLocation$stateLocation"
else
	echo "No Tor Mode"
	torLocation=""
        torStateLocal=""
	torArg=""
fi 
echo "Tor Location: $torLocation"
echo "State File Location: $torStateLocal"

if $torMode
then
	echo "Loading tor profile"
	stateFile=`curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/stateFile" -H "Metadata-Flavor: Google"`
	echo "Found tor state profile: $stateFile"
	if ! printf -- '%s' "$stateFile" | egrep -q -- "gs://"
	then
		echo "Invalid statefile location"
		exit
	fi
	gsutil cp $torStateLocal $stateFile	
fi

echo "Updating OS"
until sudo apt -y update
do
    sleep 1
done
until sudo DEBIAN_FRONTEND=noninteractive apt -yq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" dist-upgrade
do
    sudo apt -f install
    sleep 1
done
sudo npm i -g lighthouse
for i in `seq 1 24`
do
    git pull origin tor
    python wptagent.py -vvvv --server "http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal/work/" --location $location --key Nm8A8ZvT2ep6uYDBiEyIzRd1G2jQQCdm --xvfb --throttle --exit 60 --alive /tmp/wptagent $torArg $torLocation
    echo "Exited, restarting"
    sleep 10
	if $torMode
	then
		gsutil cp $torStateLocal $stateFile
	fi
done
sudo apt -y autoremove
sudo apt clean
sudo reboot
