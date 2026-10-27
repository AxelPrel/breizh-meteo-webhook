# Breizh Météo — Discord

Publication quotidienne d'une carte météo PNG dans un salon Discord via webhook.

## Données

- Open-Meteo Forecast API : https://open-meteo.com/
- Villes de référence : Brest (Finistère), Saint-Brieuc (Côtes-d'Armor), Vannes (Morbihan), Rennes (Ille-et-Vilaine).
- La carte affiche les températures minimales/maximales, le ressenti maximal, la probabilité et le cumul de précipitations, et la vitesse maximale du vent.
- Open-Meteo gratuit pour un usage non commercial ; attribution incluse sur la carte et dans le message.

## Installation sur GitHub

1. Crée un dépôt GitHub, par exemple `breizh-meteo`. Un dépôt public facilite l'usage sans frais des runners standards GitHub Actions.
2. Ajoute les fichiers de ce projet en conservant leur arborescence.
3. Dans **Settings → Secrets and variables → Actions → New repository secret**, crée :
   - Name : `DISCORD_WEBHOOK_URL`
   - Secret : l'URL complète du webhook Discord.
4. Va dans **Actions**, active les workflows si GitHub le demande, puis sélectionne **Bulletin météo Breizh**.
5. Clique sur **Run workflow** pour tester immédiatement.
6. Vérifie le salon Discord. Une fois le test réussi, le calendrier quotidien prendra le relais.

## Horaire

Le workflow est programmé à 06:30 UTC : 07:30 à Paris en hiver et 08:30 en été. GitHub Actions planifie les cron en UTC et ne permet pas directement un horaire fixe en fuseau Europe/Paris. Le démarrage peut aussi être légèrement retardé par GitHub.

## Tester en local (facultatif)

Python 3.10+ :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/ID/TOKEN'
python meteo.py
```

Ne committe jamais l'URL du webhook dans le dépôt. Si elle est exposée, régénère-la dans les paramètres du webhook Discord.

## Dépannage

- **Le workflow échoue avant le script** : vérifie que GitHub Actions est activé dans l'onglet Actions.
- **Erreur `DISCORD_WEBHOOK_URL est absente`** : vérifie le nom du secret dans les paramètres du dépôt.
- **Discord renvoie 401 ou 404** : l'URL du webhook est invalide, supprimée ou régénérée.
- **Erreur API météo** : ouvre les logs du job et réessaie ; l'API ou le réseau peut être temporairement indisponible.
- **Pas de publication automatique** : les workflows planifiés peuvent être retardés ; GitHub peut désactiver les workflows planifiés de dépôts publics inactifs pendant une longue période.
