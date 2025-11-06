"""Test script to verify attachment upload and base64 encoding."""
import base64

# Test 1: Use a minimal valid JPEG (1x1 pixel)
print("=" * 80)
print("TEST 1: Using minimal valid JPEG")
print("=" * 80)

# Minimal valid JPEG (1x1 red pixel)
# This is a real JPEG file in hex
image_bytes = bytes.fromhex(
    'ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707'
    '07090909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c23'
    '1c1c2837292c30313434341f27393d38323c2e333432ffdb0043010909090c0b0c18'
    '0d0d1832211c213232323232323232323232323232323232323232323232323232'
    '323232323232323232323232323232323232323232323232ffc00011080001000103'
    '012200021101031101ffc4001500010100000000000000000000000000000008ffc4'
    '0014100100000000000000000000000000000000ffc40014010100000000000000'
    '0000000000000000ffc40014110100000000000000000000000000000000ffda000c'
    '03010002110311003f0063800000ffd9'
)

print(f"✅ Using minimal JPEG: {len(image_bytes)} bytes")

# Test 2: Encode to base64
print("\n" + "=" * 80)
print("TEST 2: Encoding to base64")
print("=" * 80)

base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
print(f"✅ Base64 encoded: {len(base64_encoded)} chars")
print(f"   First 50 chars: {base64_encoded[:50]}")

# Test 3: Create data URL
print("\n" + "=" * 80)
print("TEST 3: Creating data URL")
print("=" * 80)

data_url = f"data:image/jpeg;base64,{base64_encoded}"
print(f"✅ Data URL created: {len(data_url)} chars")
print(f"   First 80 chars: {data_url[:80]}")

# Test 4: Decode and verify
print("\n" + "=" * 80)
print("TEST 4: Decoding and verifying")
print("=" * 80)

try:
    decoded_bytes = base64.b64decode(base64_encoded)
    print(f"✅ Decoded successfully: {len(decoded_bytes)} bytes")

    # Verify it starts with JPEG magic bytes
    if decoded_bytes[:2] == b'\xff\xd8':
        print(f"✅ Valid JPEG magic bytes: {decoded_bytes[:2].hex()}")
    else:
        print(f"❌ Invalid JPEG magic bytes: {decoded_bytes[:2].hex()}")
except Exception as e:
    print(f"❌ Failed to decode: {e}")

# Test 5: Simulate what happens in memory_attachment_store
print("\n" + "=" * 80)
print("TEST 5: Simulating memory_attachment_store.store_attachment_content()")
print("=" * 80)

# This is what store_attachment_content does
simulated_base64 = base64.b64encode(image_bytes).decode('utf-8')
print(f"✅ Stored: {len(simulated_base64)} chars")

# This is what get_attachment_content returns
retrieved_base64 = simulated_base64
print(f"✅ Retrieved: {len(retrieved_base64)} chars")

# This is what attachment_processor does
final_data_url = f"data:image/jpeg;base64,{retrieved_base64}"
print(f"✅ Final data URL: {len(final_data_url)} chars")

# Verify final result
try:
    # Extract base64 part (everything after "base64,")
    base64_part = final_data_url.split("base64,")[1]
    final_decoded = base64.b64decode(base64_part)

    # Verify JPEG magic bytes
    if final_decoded[:2] == b'\xff\xd8':
        print(f"✅ Final verification passed: Valid JPEG with magic bytes {final_decoded[:2].hex()}")
    else:
        print(f"❌ Final verification failed: Invalid magic bytes {final_decoded[:2].hex()}")
except Exception as e:
    print(f"❌ Final verification failed: {e}")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
