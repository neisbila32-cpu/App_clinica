with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Localizar e corregir a zona do entry + binding
for i in range(1229, min(1240, len(lines))):
    print(f"Linha {i+1} ANTES: '{lines[i].rstrip()}'")

# Corregir linha 1230 (entry) - debe ter 12 spaces
if 'entry = ctk.CTkEntry' in lines[1229]:
    lines[1229] = '            entry = ctk.CTkEntry(linha, placeholder_text="Resultado", width=140, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")\n'

# Corregir linha 1232 (blank) - debe existir
if i < len(lines) and not lines[1231].strip():
    lines[1231] = '\n'

# Corregir linha 1233 (comment) - 12 spaces
if 'Gatilho de status' in lines[1232]:
    lines[1232] = '            # Gatilho de status individual: actualiza ao perder o foco (FocusOut)\n'

# Corregir linha 1234 (bind) - 12 spaces
if "entry.bind('<FocusOut>'" in lines[1233]:
    lines[1233] = "            entry.bind('<FocusOut>', lambda e, ent=entry, lbl=lbl_status, ex=id_exame: self._avaliar_entry_resultado(ent, lbl, ex))\n"

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n--- DESPOIS ---")
for i in range(1229, min(1240, len(lines))):
    print(f"Linha {i+1} DESPOIS: '{lines[i].rstrip()}'")
print("[INFO] Archivo guardado")
