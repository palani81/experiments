import Foundation

/// Lightweight KSUID (K-Sortable Unique Identifier) generator.
///
/// Format: 4-byte timestamp (seconds since epoch 2014-05-13) + 16-byte random payload,
/// base62-encoded to 27 characters. Naturally sortable by creation time.
///
/// Usage:
/// ```swift
/// let id = KSUID.generate(prefix: "card") // "card_2MtCMwXZOHPSlEMDe7OYW6bRfXX"
/// let raw = KSUID.generate()               // "2MtCMwXZOHPSlEMDe7OYW6bRfXX"
/// ```
public enum KSUID {
    /// KSUID epoch: 2014-05-13T16:53:20Z (1400000000 unix seconds)
    private static let epoch: UInt32 = 1_400_000_000

    private static let base62Chars = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
    private static let encodedLength = 27

    /// Generate a new KSUID, optionally with a prefix (e.g., "card" → "card_...").
    public static func generate(prefix: String? = nil) -> String {
        let timestamp = UInt32(Date().timeIntervalSince1970) - epoch

        // 4-byte timestamp (big-endian) + 16-byte random payload = 20 bytes
        var bytes = [UInt8](repeating: 0, count: 20)
        bytes[0] = UInt8((timestamp >> 24) & 0xFF)
        bytes[1] = UInt8((timestamp >> 16) & 0xFF)
        bytes[2] = UInt8((timestamp >> 8) & 0xFF)
        bytes[3] = UInt8(timestamp & 0xFF)

        // Fill 16 random bytes
        for i in 4..<20 {
            bytes[i] = UInt8.random(in: 0...255)
        }

        let encoded = base62Encode(bytes)
        if let prefix {
            return "\(prefix)_\(encoded)"
        }
        return encoded
    }

    /// Base62-encode a 20-byte array into a 27-character string.
    /// Uses big-endian arithmetic division to produce a fixed-width output.
    private static func base62Encode(_ bytes: [UInt8]) -> String {
        // Convert bytes to a big integer (array of UInt8), then repeatedly divide by 62
        var number = bytes
        var result = [Character](repeating: "0", count: encodedLength)

        for i in stride(from: encodedLength - 1, through: 0, by: -1) {
            var remainder: UInt16 = 0
            for j in 0..<number.count {
                let value = UInt16(number[j]) + remainder * 256
                number[j] = UInt8(value / 62)
                remainder = value % 62
            }
            result[i] = base62Chars[Int(remainder)]
        }

        return String(result)
    }
}
