import re
data = open(r"C:\Users\Acer\AppData\Local\Temp\frota_analysis\frotabank_extracted\assets\index.android.bundle", "rb").read()
strings = set(re.findall(rb'[\x20-\x7e]{4,}', data))
keywords = [b'motherName', b'birthDate', b'fullName', b'professionId', b'termsToken', b'zipCode', b'password', b'/user', b'createUser', b'register', b'onboarding', b'selfie', b'documentType', b'nationality', b'gender', b'maritalStatus', b'income', b'patrimony', b'politicallyExposed', b'address']
for kw in keywords:
    matches = [s.decode(errors='replace') for s in strings if kw.lower() in s.lower()]
    if matches:
        print(f"\n=== {kw.decode()} ===")
        for m in sorted(matches)[:15]:
            print(f"  {m}")
