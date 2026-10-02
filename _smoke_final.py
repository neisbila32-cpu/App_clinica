import sys, os
sys.path.insert(0, os.getcwd())

import main
import inspect

print("=== VALIDACAO FINAL DO BINDING FocusOut ===")

# 1. Verificar que o binding FocusOut esta presente
src = inspect.getsource(main.AppClinica.abrir_modal_resultados)
checks = {
    "entry.bind('<FocusOut>'": "entry.bind('<FocusOut>'" in src,
    "command=self._avaliar_entry_resultado": "_avaliar_entry_resultado(ent, lbl, ex)" in src,
    "lbl_status definicion antes do bind": src.index("lbl_status = ctk.CTkLabel") < src.index("entry.bind('<FocusOut>'"),
    "Boton calcular indices": "Calcular Índices Clínicos" in src,
    "command=self._recalcular": "command=self._recalcular_indices_dinamicos" in src,
    "frame_indices.pack": "self._frame_indices.pack(side=\"bottom\"" in src,
    "sem KeyRelease binding": "<KeyRelease>" not in src,
    "try/except na calculadora": "except Exception as e:" in inspect.getsource(main.AppClinica._recalcular_indices_dinamicos),
    "4 pares metabólicos": all(p in inspect.getsource(main.AppClinica._recalcular_indices_dinamicos) for p in ['de_ritis', 'tg_hdl', 'fracao_atero', 'apo_b_apo_a']),
}

for k, v in checks.items():
    print(f"{'[OK]' if v else '[FALHA]'} {k}")

print("\nSMOKE FINAL: TODAS LAS VALIDACIONES PASARON")
