# App2 — accès au formulaire

Application web Flask destinée à être déployée sur Render. Elle demande un
identifiant et un **code d'accès dédié** (jamais le mot de passe d'un compte),
puis redirige les personnes autorisées vers le formulaire configuré.
Le classeur Excel local est conservé sur l'ordinateur, ignoré par Git et n'est
pas utilisé par le site web.

## Déployer sur Render

1. Poussez ces fichiers sur GitHub. Le dépôt doit contenir `render.yaml` à sa
   racine.
2. Dans Render, choisissez **New > Blueprint** et connectez le dépôt GitHub.
   Render lira `render.yaml` et créera le service web.
3. Lors de la configuration, fournissez les variables d'environnement :
   - `FORM_URL` : lien HTTPS complet du formulaire.
   - `ACCESS_CODES_JSON` : objet JSON associant chaque identifiant à un code
     d'accès dédié, par exemple `{"membre01":"code-aleatoire-long"}`.
4. Déployez et ouvrez l'URL `onrender.com` affichée par Render.

Ne mettez jamais ces valeurs dans GitHub, dans le code ou dans une capture
d'écran. Modifiez-les depuis **Render > service > Environment**. Changer
`FORM_URL` ou `ACCESS_CODES_JSON` depuis Render déclenche un redéploiement du
service.

Utilisez un code aléatoire long et différent par personne. Pour retirer un
accès, supprimez l'identifiant correspondant de `ACCESS_CODES_JSON`.

## Développement local

Depuis le dossier `dossier`, installez les dépendances et définissez les deux
variables d'environnement avant de lancer `python app.py`. En PowerShell :

```powershell
python -m pip install -r requirements.txt
$env:FORM_URL = "https://example.org/formulaire"
$env:ACCESS_CODES_JSON = '{"membre01":"remplacer-par-un-code-aleatoire-long"}'
python app.py
```

Ouvrez ensuite `http://127.0.0.1:5000`.

## Limites du forfait gratuit

Le service web gratuit peut s'endormir lorsqu'il n'est pas utilisé et le
premier chargement suivant peut être lent. Cette configuration ne nécessite
pas de base de données : la liste des accès et le lien sont des variables
Render. Les fichiers locaux du service gratuit ne sont pas un stockage
persistant. Render indique également que ses bases PostgreSQL gratuites
expirent après 30 jours ; ce déploiement n'en crée donc pas.

Le contrôle par l'application ne remplace pas les permissions configurées dans
Microsoft Forms. Si le formulaire autorise les réponses anonymes, une personne
qui possède directement son URL peut toujours l'ouvrir.
