import re
data = open(r"C:\Users\Acer\AppData\Local\Temp\frota_analysis\frotabank_extracted\assets\index.android.bundle", "rb").read()
# Extract all printable strings of 6+ chars
strings = re.findall(rb'[\x20-\x7e]{6,200}', data)
# Filter for registration-related
keywords = [b'motherName', b'birthDate', b'fullName', b'professionId', b'termsToken', b'password', b'/user', b'selfie', b'documentType', b'nationality', b'gender', b'maritalStatus', b'income', b'patrimony', b'politicallyExposed', b'PersonalData', b'Registration', b'createAccount', b'signUp', b'onboarding']
found = {}
for s in strings:
    sl = s.lower()
    for kw in keywords:
        if kw.lower() in sl:
            if kw not in found:
                found[kw] = []
            if len(found[kw]) < 10:
                found[kw].append(s.decode(errors='replace'))
for kw in keywords:
    if kw in found:
        print(f"\n=== {kw.decode()} ===")
        for m in found[kw]:
            print(f"  {m}")
