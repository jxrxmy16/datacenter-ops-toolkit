"""Vocabulario ampliado del intérprete de texto libre (generado, no se edita a mano).

Se compila con `tools/compilar_vocabulario.py` a partir de los ficheros de
vocabulario por intención. Cada intención tiene:

  verbos   infinitivos ("almorzar", "almorzar|almuerz" con raíces irregulares,
           "tomar:0.6" con peso); se derivan las raíces de sus formas;
  raices   prefijos de 4 o más letras ("guantaz", "mendrug:0.5");
  exactas  palabras enteras ("tentempie");
  frases   [[raíces cercanas...], peso]  (véase lenguaje.FRASES).
"""

VOCABULARIO = {}
