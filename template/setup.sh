#!/bin/bash -e
if [ `basename $(pwd)` != "template" ]; then
    echo "script should be run from template folder" 1>&2
    exit 233
fi

echo "Make sure you have "
echo " - set the administator account"
echo " - installed python3 on host machine but not docker image"
echo " - pip3 and python3 can be run on host machine"
echo " - port of container is exposed"
echo " - mounted the volume"
echo ""
read -p "Have you written config file manually? (default: no)" A
A=${A:-no}
if [ $A != 'y' ]; then
    echo "OK, we'll create one"
    read -p "Email:" EMAIL
    read -p "Password:" PASSWD
    echo "Config server"
    read -p "Server address with port: (pess enter to use 127.0.0.1:5000)" SERVER
    SERVER=${SERVER:-127.0.0.1:5000}
    read -p "Server protocol: (press enter to use http)" PROTOCOL
    PROTOCOL=${PROTOCOL:-http}

    cp -f config.ini.example config.ini
    sed -i "s|^EMAIL.*$|EMAIL = ${EMAIL}|" config.ini
    sed -i "s|^PASSWORD.*$|PASSWORD = ${PASSWD}|" config.ini
    sed -i "s|^IP.*$|IP = ${SERVER}|" config.ini
    sed -i "s|^PROTOCOL.*$|PROTOCOL = ${PROTOCOL}|" config.ini
fi

echo "Check config.ini before continue"
echo "================================="
cat config.ini
echo ""
echo "================================="
echo ""
echo -n "Press SPACE to continue or Ctrl+C to exit ... "
while true; do
   IFS= read -n1 -r key
   [[ $key == ' ' ]] && break
done
echo ""

pip3 install -r requirements.txt
python3 qiandao_template.py --upload