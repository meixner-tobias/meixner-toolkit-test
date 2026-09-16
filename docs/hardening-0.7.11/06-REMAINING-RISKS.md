# Verbleibende Risiken 0.7.11

1. **Core-Master sind bewusst nicht live-verifiziert:** Die ausgelieferten Web-/Server-Core-Dateien sind `candidate_reference_only`. Der erste echte GTM Import/Preview/Re-Export muss noch durch Tobias erfolgen; erst danach darf ein Verified-Manifest registriert werden.
2. **Community Templates ändern sich:** Die Referenz enthält Strukturwissen zu einer real verwendeten Stape-CAPI-Template-Version. Vor neuem Kundenaufbau aktuelle Gallery-/Stape-Dokumentation prüfen; keine alte Template-ID aus Erinnerung erzwingen.
3. **Consent ist kunden- und regionsabhängig:** Die Referenzkonfiguration ist kein rechtlicher oder technischer Default. Das Completeness Gate reduziert Fehlkonfigurationen, ersetzt aber keine aktuelle CMP-/Rechtsprüfung.
4. **Quellsignale können fragil sein:** CSS-/Text-Klicktrigger aus einem Produktionsbeispiel sind kein Universalpattern. Callback/dataLayer/erfolgreiche Backend-/Frontend-Bestätigung ist bevorzugt.
5. **Browser-E2E der 0.7.11:** Der exakte Playwright-1.56.1-Chromium-Lauf konnte in der Build-Sandbox wegen nicht verfügbarem npm-Registry-Zugriff nicht installiert/ausgeführt werden. GitHub Actions muss vor Production-Freigabe grün sein.
6. **Offengelegter Originaltoken:** Ein Token, der bereits in einem exportierten/hochgeladenen Original vorkam, muss beim Anbieter rotiert werden; Sanitization kann eine frühere Offenlegung nicht rückgängig machen.
7. **Test-Orchestrierung:** Jeder Testblock ist isoliert lauffähig und 221/221 Assertions sind grün. Auf stark eingeschränkten Sandboxes kann das wiederholte Starten sehr vieler Child-Prozesse selbst limitiert sein; CI führt deshalb die isolierten Blöcke aus und ist der externe Release-Beleg.
