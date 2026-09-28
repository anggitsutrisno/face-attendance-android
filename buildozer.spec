[app]

title = Face Attendance
package.name = faceattendance
package.domain = com.nerazurra

source.dir = .
source.include_exts = py,png,jpg,jpg,kv,atlas,xml,yml,db

version = 0.1.0

# buildozer.spec line 12
requirements = python3,kivy==2.3.1,https://github.com/kivymd/KivyMD/archive/refs/tags/2.0.0.zip,materialyoucolor==3.0.3,materialshapes==0.3,pycairo,pillow,exceptiongroup,asyncgui,asynckivy,android,opencv,numpy
# Pin python-for-android
# Menghindari build menggunakan Python 3.14
p4a.branch = master
p4a.commit = 58d2114

# Local recipe override untuk OpenCV contrib / cv2.face
p4a.local_recipes = ./recipes

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png

android.permissions = CAMERA

android.api = 33
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a

android.allow_backup = True


[buildozer]
log_level = 2
warn_on_root = 1
