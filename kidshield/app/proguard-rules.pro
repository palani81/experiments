# KidShield ProGuard Rules

# Keep Device Admin Receiver
-keep class com.kidshield.tv.service.KidShieldDeviceAdminReceiver { *; }

# Keep Room entities
-keep class com.kidshield.tv.data.model.** { *; }

# Bcrypt
-keep class at.favre.lib.crypto.** { *; }
