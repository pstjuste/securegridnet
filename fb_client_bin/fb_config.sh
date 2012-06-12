#!/bin/sh

if [ ! -f /mnt/fd/fb_done ] 
then
  echo 'Starting Facebook reconfiguration tool'
  cd /usr/local/fbsample/
  python manage.py runserver 0.0.0.0:8080 &> http_log.txt &
  echo 'Running HTTP server at 0.0.0.0:8080'
  echo 'Please go to http://apps.facebook.com/securegridnet/ to configure your node'

  while [ ! -f /mnt/fd/fb_done ]  
  do
    sleep 30
  done

  echo 'Facebook reconfiguration tool has updated you network configurations'
fi

