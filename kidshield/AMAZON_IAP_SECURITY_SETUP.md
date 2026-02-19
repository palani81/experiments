# Amazon IAP Security Setup Guide

## Overview

Amazon IAP uses a public/private key pair system for secure communication between your app and the Amazon Appstore. This ensures that only authorized users can access your app's premium features.

## Security Requirements

### 1. Public Key Authentication
- **Purpose**: Establishes secure communication channel
- **Location**: Must be placed in `app/src/main/assets/AppstoreAuthenticationKey.pem`
- **Source**: Downloaded from Amazon Developer Console

### 2. Certificate Hash Validation
- **Purpose**: Validates app signature and prevents tampering
- **Automatic**: Handled by Amazon Appstore SDK
- **Required for**: Production releases

## Setup Steps

### Step 1: Download Public Key from Amazon Developer Console

1. **Sign in to Amazon Developer Console**
   - Go to https://developer.amazon.com
   - Navigate to Apps & Services > My Apps

2. **Select Your App**
   - Click on your KidShield app
   - Create a new version if needed (click "Upcoming Version")

3. **Download Public Key**
   - Go to "Upload Your App File" screen
   - In "Additional information" section, click "View public key"
   - Download the `AppstoreAuthenticationKey.pem` file

4. **Add to Project**
   - Create `app/src/main/assets` folder if it doesn't exist
   - Copy `AppstoreAuthenticationKey.pem` to this folder

### Step 2: Verify Certificate Hashes (Production Only)

For production releases, you can find your certificate hashes in:
- Developer Console > My Apps > [Your App] > Upload Your App File > Appstore Certificate Hashes

## Current Implementation Status

### ✅ What's Already Implemented
- Amazon Appstore SDK integration via Maven Central
- IAP service initialization and registration
- Purchase flow handling
- Subscription state management
- Error handling for purchase responses

### ⚠️ What's Missing
- **Public Key File**: `AppstoreAuthenticationKey.pem` not yet added
- **Production Certificate**: Will be handled by Amazon during app submission

### 🔧 What Needs to Be Done

1. **Add Public Key File** (Required for testing and production)
2. **Test with Amazon App Tester** (Requires public key)
3. **Production Submission** (Amazon handles certificate signing)

## Security Flow

### Development/Testing
```
1. App starts → IAP Manager initializes
2. SDK reads public key from assets folder
3. Establishes secure connection to Amazon Appstore
4. Validates subscription SKUs
5. Processes purchase requests securely
```

### Production
```
1. Amazon re-signs app with unique certificate
2. Certificate hash validates app authenticity
3. Public/private key pair ensures secure communication
4. All IAP transactions are cryptographically verified
```

## Implementation Notes

### Current IAP Manager Security
Our `AmazonIapManager` already handles:
- Secure purchase validation
- Receipt verification (handled by Amazon)
- Error handling for security failures
- Proper state management

### What Amazon Handles Automatically
- Receipt validation and verification
- Subscription renewal management
- Payment processing security
- Certificate validation
- Anti-tampering protection

### What We Handle
- Public key integration
- Purchase flow UI/UX
- Error handling and user feedback
- Subscription state management
- Premium feature access control

## Testing Security

### With Amazon App Tester
1. Install App Tester on Fire TV device
2. Configure test accounts in Developer Console
3. Test purchase flows in sandbox mode
4. Verify security errors are handled properly

### Security Test Cases
- Invalid public key (should fail gracefully)
- Network interruption during purchase
- Invalid SKU attempts
- Subscription validation
- Receipt tampering detection (handled by Amazon)

## Production Deployment

### Amazon Appstore Submission
1. **App Signing**: Amazon re-signs with unique certificate
2. **Security Validation**: Automatic certificate hash validation
3. **IAP Integration**: Public key enables secure communication
4. **Monitoring**: Amazon provides security analytics

### Post-Launch Security
- Monitor subscription metrics for anomalies
- Track failed purchase attempts
- Review security logs in Amazon Developer Console
- Update public key if needed (rare)

## Security Best Practices

### Code Security
- Never hardcode sensitive data
- Use ProGuard/R8 for code obfuscation
- Validate all user inputs
- Handle security errors gracefully

### IAP Security
- Always validate receipts (handled by Amazon)
- Check subscription status server-side if needed
- Implement proper error handling
- Use secure communication channels only

### User Privacy
- Follow Amazon's privacy guidelines
- Secure user subscription data
- Implement proper data retention policies
- Provide clear privacy disclosures

## Troubleshooting Security Issues

### Common Issues
1. **"Invalid public key"** → Check file location and format
2. **"Purchase not supported"** → Verify app signing and certificates
3. **"Network error"** → Check device connectivity and Amazon services
4. **"Invalid SKU"** → Verify SKUs match Developer Console exactly

### Debug Steps
1. Check logcat for IAP security errors
2. Verify public key file exists in assets
3. Test with Amazon App Tester
4. Validate SKUs in Developer Console
5. Check app signing configuration

## Next Steps

1. **Immediate**: Add placeholder for public key file
2. **Testing**: Download actual public key from Developer Console
3. **Production**: Submit app to Amazon Appstore
4. **Monitoring**: Track security metrics post-launch

This security setup ensures that your KidShield app's premium subscriptions are protected against unauthorized access and tampering.