# Modelo A/B en partida

- Modelo A es el predeterminado y el modelo principal.
- El operador puede cambiar a Modelo B entre partidas.
- No se permite cambiar el modelo después de que una partida ya tenga bolas jugadas.
- La verificación no confía únicamente en el selector: recupera el cartón por serial y valida su `CardModel` y su matriz exacta.
- Si el modelo de la partida y el del cartón no coinciden, la verificación se detiene con un aviso de incompatibilidad.
- Línea y bingo se calculan sobre los números reales almacenados en ese cartón.
