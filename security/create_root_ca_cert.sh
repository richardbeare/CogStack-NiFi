#!/bin/bash

################################################################
# 
# This script generates the root CA key and certificate
#

set -e

if [[ -z "${ROOT_CERTIFICATE_NAME}" ]]; then
    ROOT_CERTIFICATE_NAME="root-ca"
    echo "ROOT_CERTIFICATE_NAME not set, defaulting to ROOT_CERTIFICATE_NAME=root-ca"
else
    ROOT_CERTIFICATE_NAME=${ROOT_CERTIFICATE_NAME}
fi

if [[ -z "${ROOT_CERTIFICATE_KEY_PASSWORD}" ]]; then
    ROOT_CERTIFICATE_KEY_PASSWORD="cogstackNifi"
    echo "ROOT_CERTIFICATE_KEY_PASSWORD not set, defaulting to ROOT_CERTIFICATE_KEY_PASSWORD=cogstackNifi"
else
    ROOT_CERTIFICATE_KEY_PASSWORD=${ROOT_CERTIFICATE_KEY_PASSWORD}
fi

if [[ -z "${ROOT_CERTIFICATE_SUBJ_LINE}" ]]; then
    ROOT_CERTIFICATE_SUBJ_LINE="/C=UK/ST=UK/L=UK/O=cogstack/OU=cogstack/CN=cogstack"
    echo "ROOT_CERTIFICATE_SUBJ_LINE not set, defaulting to ROOT_CERTIFICATE_SUBJ_LINE=/C=UK/ST=UK/L=UK/O=cogstack/OU=cogstack/CN=cogstack"
else
    ROOT_CERTIFICATE_SUBJ_LINE=${ROOT_CERTIFICATE_SUBJ_LINE}
fi

if [[ -z "${ROOT_CERTIFICATE_ALIAS_NAME}" ]]; then
    ROOT_CERTIFICATE_ALIAS_NAME=$ROOT_CERTIFICATE_NAME
    echo "ROOT_CERTIFICATE_ALIAS_NAME not set, defaulting to ROOT_CERTIFICATE_ALIAS_NAME=$ROOT_CERTIFICATE_NAME"
else
    ROOT_CERTIFICATE_ALIAS_NAME=${ROOT_CERTIFICATE_ALIAS_NAME}
fi

if [[ -z "${ROOT_CERTIFICATE_TIME_VAILIDITY_IN_DAYS}" ]]; then
    ROOT_CERTIFICATE_TIME_VAILIDITY_IN_DAYS=730
    echo "ROOT_CERTIFICATE_TIME_VAILIDITY_IN_DAYS not set, defaulting to ROOT_CERTIFICATE_TIME_VAILIDITY_IN_DAYS=730"
else
    ROOT_CERTIFICATE_TIME_VAILIDITY_IN_DAYS=${ROOT_CERTIFICATE_TIME_VAILIDITY_IN_DAYS}
fi

CA_ROOT_CERT=$ROOT_CERTIFICATE_NAME".pem"
CA_ROOT_KEY=$ROOT_CERTIFICATE_NAME".key"

if [[ -z "${ROOT_CERTIFICATE_KEY_SIZE}" ]]; then
    ROOT_CERTIFICATE_KEY_SIZE=4096
    echo "ROOT_CERTIFICATE_KEY_SIZE not set, defaulting to ROOT_CERTIFICATE_KEY_SIZE=4096"
else
    ROOT_CERTIFICATE_KEY_SIZE=${ROOT_CERTIFICATE_KEY_SIZE}
fi

echo "Generating root CA key"
openssl genrsa -out $CA_ROOT_KEY $ROOT_CERTIFICATE_KEY_SIZE

echo "Generating root CA cert"
openssl req -x509 -new -key $CA_ROOT_KEY -sha256 -out $CA_ROOT_CERT -days $ROOT_CERTIFICATE_TIME_VAILIDITY_IN_DAYS -subj $ROOT_CERTIFICATE_SUBJ_LINE

# create p12 version manually
echo "Generation pkcs12 keystore"
openssl pkcs12 -export -out root-ca.p12 -inkey root-ca.key -in root-ca.pem -passin pass:$ROOT_CERTIFICATE_KEY_PASSWORD -passout pass:$ROOT_CERTIFICATE_KEY_PASSWORD -name $ROOT_CERTIFICATE_ALIAS_NAME
