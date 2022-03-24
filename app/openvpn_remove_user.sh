# ! /bin/bash
set -e
OVPN_USER_KEYS_DIR=/etc/openvpn/client/keys
EASY_RSA_DIR=/etc/openvpn/easy-rsa/

revoke(){
  CRL="crl.pem"
  RT="revoke-test.pem"

  if [ "$KEY_DIR" ]; then
      cd "$KEY_DIR"
      rm -f "$RT"

      # set defaults
      export KEY_CN=""
      export KEY_OU=""
      export KEY_NAME=""

    # required due to hack in openssl.cnf that supports Subject Alternative Names
      export KEY_ALTNAMES=""

      # revoke key and generate a new CRL
      $OPENSSL ca -revoke "$1.crt" -config "$KEY_CONFIG"
      # generate a new CRL -- try to be compatible with
      # intermediate PKIs
      $OPENSSL ca -gencrl -out "$CRL" -config "$KEY_CONFIG"
      if [ -e export-ca.crt ]; then
          cat export-ca.crt "$CRL" >"$RT"
      else
          cat ca.crt "$CRL" >"$RT"
      fi
      # verify the revocation
      # $OPENSSL verify -CAfile "$RT" -crl_check "$1.crt"
      cd ..
  fi
}

for user in "$@"
do
  cd $EASY_RSA_DIR
  source ./vars

  # 吊销证书
  revoke $user
  for i in `./list-crl | grep 'Serial Number:' | cut -d: -f2 | xargs`;do rm -f "./keys/$i.pem"; done
  # 清理客户端相关文件

  if [ -f "/etc/openvpn/ccd/$user" ]; then
    rm -rf "/etc/openvpn/ccd/$user.crt"
  fi

  if [ -f "$EASY_RSA_DIR/keys/$user.crt" ]; then
    rm -rf "$EASY_RSA_DIR/keys/$user.crt"
  fi

  if [ -f "$EASY_RSA_DIR/keys/$user.csr" ]; then
    rm -rf "$EASY_RSA_DIR/keys/$user.csr"
  fi

  if [ -f "$EASY_RSA_DIR/keys/$user.key" ]; then
    rm -rf "$EASY_RSA_DIR/keys/$user.key"
  fi
#  chmod 755 $EASY_RSA_DIR/keys
done
exit 0