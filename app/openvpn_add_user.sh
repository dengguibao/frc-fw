# ! /bin/bash
set -e

OVPN_USER_KEYS_DIR=/etc/openvpn/client/keys
EASY_RSA_DIR=/etc/openvpn/easy-rsa/
PKI_DIR=$EASY_RSA_DIR/keys

for user in "$@"
do
  if [ -d "$OVPN_USER_KEYS_DIR/$user" ]; then
    rm -rf $OVPN_USER_KEYS_DIR/$user
  fi
  cd $EASY_RSA_DIR
  source ./vars
  # 生成客户端SSL证书文件
  ./build-key --batch $user
  # 整理下生成的文件
#  mkdir -p  $OVPN_USER_KEYS_DIR/$user
#  cp $PKI_DIR/ca.crt $OVPN_USER_KEYS_DIR/$user/   # CA 根证书
#  cp $PKI_DIR/$user.crt $OVPN_USER_KEYS_DIR/$user/   # 客户端证书
#  cp $PKI_DIR/$user.key $OVPN_USER_KEYS_DIR/$user/  # 客户端证书密钥
done
#chmod 755 $PKI_DIR
exit 0