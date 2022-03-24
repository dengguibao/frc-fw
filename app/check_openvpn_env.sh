#!/bin/bash
set -e

OPENVPN_CONFIG_DIR=/etc/openvpn
EASY_RSA_DIR=$OPENVPN_CONFIG_DIR/easy-rsa

[[ -f $EASY_RSA_DIR/keys/crl.pem ]] && echo 'found crl.pem' ||  (echo 'not found crl.pem, please manual build!'&&exit 1)
[[ -f $OPENVPN_CONFIG_DIR/ca.crt ]] && echo 'found ca.crt' ||  (echo 'not found ca.crt, please manual build ca cert!'&&exit 1)
[[ -d $OPENVPN_CONFIG_DIR/ccd ]] && echo 'found ccd folder' ||  mkdir -p $OPENVPN_CONFIG_DIR/ccd
[[ -f $OPENVPN_CONFIG_DIR/openvpn-server.crt ]] && echo 'found openvpn-server.crt' || (echo 'not found ca.crt, please manual build!'&&exit 1)
[[ -f $OPENVPN_CONFIG_DIR/openvpn-server.key ]] && echo 'found openvpn-server.key' || (echo 'not found ca.crt, please manual build!'&&exit 1)
[[ -f $OPENVPN_CONFIG_DIR/ta.key ]] && echo 'found ta.key' || (cd OPENVPN_CONFIG_DIR && openvpn --genkey --secret ta.key && echo 'build tls-auth key success!')
[[ -f $OPENVPN_CONFIG_DIR/dh1024.pem ]] && echo 'found dh2048.pem' || (echo 'not found dh2048.key, please manual build!'&&exit 1)
chmod o+r $EASY_RSA_DIR/keys/crl.pem
echo 'all environment already!'
exit 0