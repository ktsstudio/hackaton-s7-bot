#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p $DIR/large

curl http://ling.go.mail.ru/static/models/ruscorpora_russe.model.bin.gz > $DIR/large/ruscorpora_russe.model.bin.gz
#curl http://ling.go.mail.ru/static/models/web_russe.model.bin.gz > $DIR/large/web_russe.model.bin.gz

cd $DIR/large
echo "gunzip ruscorpora_russe.model.bin.gz"
gunzip ruscorpora_russe.model.bin.gz

#echo "gunzip web_russe.model.bin.gz"
#gunzip web_russe.model.bin.gz
