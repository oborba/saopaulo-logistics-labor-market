# Mobile Optimization Tasks

## Global / Shared
- [x] **Map Interaction**: Disable `scrollWheelZoom` on all Folium maps to prevent scroll trapping on mobile devices.

## pages/Overview.py
- [ ] **Heatmap Performance**: Aggregate data points or adjust opacity/radius to improve rendering performance on mobile GPUs.
- [ ] **Metrics Layout**: Review `st.columns(3)` usage; consider stacking metrics or simplifying content for narrow screens.

## pages/LogisticsBlackout.py
- [ ] **Chart Touch UX**: Configure Plotly `hovermode` (e.g., to 'x unified') and margins for better touch interaction.
- [ ] **Dataframe Replacement**: Replace the large risk `st.dataframe` with a simplified "Top 5" static list or metric view for better readability.
- [ ] **CSS Units**: Refactor custom CSS to use `rem` instead of `px` for font sizes to respect accessibility settings.
- [ ] **Responsive Cards**: Ensure HTML/CSS recommendation cards handle variable heights gracefully when stacked on mobile.

## Future / Strategic
- [ ] **StrategicPlanning.py**: Create a new page for specific regional actions based on risk data.
- [ ] **Refactoring**: Move common data loading logic to `utils.py`.
