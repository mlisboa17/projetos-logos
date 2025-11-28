[app]
title = VerifiK Mobile
package.name = verifik_coleta
package.domain = com.logos.verifik

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,db

version = 1.0
requirements = python3,kivy==2.3.0,pillow
icon.filename = icon.png

[buildozer]
log_level = 1
warn_on_root = 0

[app:android]
archs = armeabi-v7a
api = 33
minapi = 21
ndk = 25b
accept_sdk_license = True
