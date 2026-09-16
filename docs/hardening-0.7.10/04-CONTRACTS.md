# Verträge 0.7.10

- Consent-Szenario (`emptyScenario`): Arrays wie `hits`, `cookies_before`, `cookies_after`, `blockiert` existieren immer; Storage-Felder existieren mindestens als `null`; `status` beginnt als `unknown`.
- Report-Output: nur unter erlaubtem realen Parent-Pfad; `.part` exklusiv; kein Folgen von Symlinks; HTML und PDF nutzen denselben sicheren Writer.
- `Builder(..., server_resolver=None)`: Produktivpfad nutzt Systemresolver, Tests können einen Resolver injizieren; `server_container_url` muss auf ausschließlich global erreichbare IPs zeigen.
- Google Consent: `gcs`/`gcd` = beobachtete codierte Evidenz; keine fest eingebaute Granted/Denied-Stringtabelle.
- Browser-Netzpolicy: Transition-/Translation-Netze werden konservativ behandelt; WebSocket-/Service-Worker-Regeln aus 0.7.9 bleiben unverändert.
