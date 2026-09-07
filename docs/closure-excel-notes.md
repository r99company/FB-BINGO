# Cierre de partida y Excel

El botón FINALIZAR cierra la partida activa en SQLite y genera su reporte Excel. El historial queda disponible desde REPORTES para volver a exportar cualquier partida guardada.

El flujo conserva las bolas digitadas por la locutora, permite finalizar incluso una partida sin bolas y mantiene la interfaz neón aprobada sin cambios de diseño.

## Flujo operativo

1. La locutora digita cada bola extraída físicamente.
2. FB-BINGO la registra en el historial de la partida.
3. FINALIZAR marca la partida como `finalizada`.
4. Se genera el Excel automáticamente.
5. REPORTES permite consultar y volver a exportar partidas guardadas.
