# 📋 Changelog - Gestionnaire de Disques

## Version 02 (Décembre 2025)

### 🆕 Nouvelles Fonctionnalités Majeures

#### 📂 Explorateur de Fichiers Avancé
- **Navigation complète** du système de fichiers
- **9 colonnes d'informations détaillées** :
  - Nom avec icônes contextuelles (30+ types de fichiers)
  - Taille formatée automatiquement
  - Type de fichier
  - Propriétaire (utilisateur)
  - Groupe propriétaire
  - Permissions Unix (format rwxrwxrwx)
  - Date de modification
  - Date de création/changement
  - Date de dernier accès
- **Barre de navigation** avec boutons :
  - Retour (historique de navigation)
  - Parent (dossier parent)
  - Accueil (dossier personnel)
  - Actualiser
- **Recherche/Filtrage en temps réel**
- **Menu contextuel** :
  - Ouvrir
  - Propriétés détaillées
  - Copier le chemin dans le presse-papier
- **Tri par colonne** (clic sur en-têtes)
- **Couleurs différenciées** (dossiers en bleu gras)
- **Double-clic intelligent** :
  - Dossier → Navigation
  - Fichier → Affichage des propriétés

#### ⚙️ Gestionnaire de Processus
- **Liste complète des processus** avec 8 colonnes :
  - PID (Process ID)
  - Nom du processus
  - Utilisateur propriétaire
  - Utilisation CPU (%)
  - Utilisation mémoire (%)
  - Mémoire en MB
  - État du processus
  - Ligne de commande complète
- **Actualisation automatique** toutes les 3 secondes
- **Statistiques système en temps réel** :
  - Utilisation CPU globale
  - Utilisation mémoire (% et valeurs absolues)
  - Nombre total de processus
- **Codes couleur intelligents** :
  - Rouge : Utilisation élevée (>50% CPU ou >10% RAM)
  - Orange : Utilisation moyenne (>20% CPU ou >5% RAM)
  - Vert : État "running"
  - Bleu : État "sleeping"
- **Filtrage par nom** de processus
- **Menu contextuel** :
  - Détails complets du processus
  - Terminer le processus (avec confirmation)
- **Tri par colonne** (par défaut : CPU décroissant)

#### 🔗 Intégration Améliorée
- **Bouton "Explorer"** sur les disques montés
  - Ouvre directement l'explorateur sur le point de montage
  - Bascule automatiquement vers l'onglet explorateur
- **Interface unifiée** : Tous les outils dans une seule application

### 🎨 Améliorations de l'Interface

- **Design modernisé** avec boutons colorés et stylisés
- **Icônes emoji** pour meilleure lisibilité
- **Barres d'information** contextuelles
- **Alternance de couleurs** dans les tables
- **Redimensionnement intelligent** des colonnes
- **Splitter ajustable** entre sections

### 🔧 Améliorations Techniques

- **Module psutil** pour gestion des processus
- **Module pwd/grp** pour informations utilisateurs/groupes
- **Module stat** pour décodage des permissions
- **QTimer** pour actualisation automatique
- **Gestion d'historique** pour navigation
- **Gestion des exceptions** améliorée
- **Performance optimisée** (limite de 200 processus)

### 📚 Documentation

- **README.md complet** avec exemples détaillés
- **GUIDE_RAPIDE.txt** pour démarrage rapide
- **Scripts d'installation et lancement**
- **Fichier requirements.txt** pour dépendances

---

## Version 01 (Novembre 2025)

### Fonctionnalités Initiales

#### Gestion des Disques
- Détection automatique des disques via lsblk
- Montage/Démontage avec sudo
- Modes lecture seule et lecture-écriture
- Support NTFS via ntfs-3g
- Filtrage des partitions système

#### Visualisations
- **Graphique circulaire (Pie Chart)** :
  - Top 10 des plus gros éléments
  - Pourcentages et tailles
  - Catégorie "Autres"
- **TreeMap interactif** :
  - Visualisation rectangulaire proportionnelle
  - Navigation par clic
  - Boutons retour/racine
  - Effets visuels (ombres, gradients)
  - Légende avec top 12 éléments
  - Top 30 éléments affichés
- **Arborescence hiérarchique** :
  - Navigation dans les dossiers
  - Tri par taille
  - Limite de 50 éléments par niveau

#### Analyse
- **Thread d'analyse** non bloquant
- **Profondeur configurable** (défaut: 3 niveaux)
- **Barre de progression**
- **Gestion des permissions**

#### Interface
- **PyQt5** avec style Fusion
- **Splitter vertical** ajustable
- **Onglets** pour différentes vues
- **Logs horodatés**
- **Confirmations** avant actions critiques

---

## 🔄 Comparaison V01 vs V02

| Fonctionnalité | V01 | V02 |
|----------------|-----|-----|
| **Gestion des disques** | ✅ | ✅ |
| **Montage/Démontage** | ✅ | ✅ |
| **Graphique circulaire** | ✅ | ✅ |
| **TreeMap interactif** | ✅ | ❌ |
| **Arborescence** | ✅ | ❌ |
| **Explorateur de fichiers** | ❌ | ✅ ⭐ |
| **Détails fichiers (9 colonnes)** | ❌ | ✅ ⭐ |
| **Permissions Unix** | ❌ | ✅ ⭐ |
| **Propriétaire/Groupe** | ❌ | ✅ ⭐ |
| **Dates (modif/création/accès)** | ❌ | ✅ ⭐ |
| **Navigation avec historique** | ❌ | ✅ ⭐ |
| **Recherche/Filtrage** | ❌ | ✅ ⭐ |
| **Menu contextuel** | ❌ | ✅ ⭐ |
| **Gestionnaire de processus** | ❌ | ✅ ⭐ |
| **Surveillance CPU/RAM** | ❌ | ✅ ⭐ |
| **Terminer processus** | ❌ | ✅ ⭐ |
| **Actualisation auto** | ❌ | ✅ ⭐ |
| **Icônes par type** | ❌ | ✅ ⭐ |
| **Codes couleur** | Partiel | ✅ Complet |
| **Bouton Explorer** | ❌ | ✅ ⭐ |
| **Logs** | ✅ | ✅ |

⭐ = Nouvelle fonctionnalité V02

---

## 📊 Statistiques

### Version 01
- **Lignes de code** : ~1100
- **Classes** : 6
- **Onglets** : 4
- **Dépendances** : PyQt5, matplotlib, squarify

### Version 02
- **Lignes de code** : ~1600
- **Classes** : 6
- **Onglets** : 4
- **Dépendances** : PyQt5, matplotlib, psutil
- **Nouvelles fonctionnalités** : 15+

---

## 🎯 Objectifs Atteints

### V02
✅ Explorateur de fichiers complet avec toutes les métadonnées  
✅ Gestionnaire de processus avec surveillance en temps réel  
✅ Navigation intuitive avec historique  
✅ Recherche et filtrage instantanés  
✅ Affichage des permissions Unix  
✅ Menu contextuel pour actions rapides  
✅ Intégration complète avec gestion des disques  
✅ Documentation exhaustive  
✅ Scripts d'installation automatisés  

---

## 🚀 Évolutions Futures Possibles

### Court Terme
- [ ] Édition des permissions de fichiers
- [ ] Copier/Coller/Déplacer des fichiers
- [ ] Aperçu de fichiers (images, texte)
- [ ] Recherche avancée (taille, date, type)

### Moyen Terme
- [ ] Graphiques d'utilisation CPU/RAM dans le temps
- [ ] Export de la liste des fichiers en CSV
- [ ] Favoris/Signets de dossiers
- [ ] Compression/Décompression d'archives
- [ ] Calcul de checksums (MD5, SHA256)

### Long Terme
- [ ] Comparaison de dossiers
- [ ] Synchronisation de fichiers
- [ ] Éditeur de texte intégré
- [ ] Terminal intégré
- [ ] Thèmes personnalisables
- [ ] Support multi-langues

---

## 🐛 Corrections de Bugs

### V02
- Amélioration de la gestion des erreurs de permissions
- Meilleur formatage des tailles (unités cohérentes)
- Gestion des processus zombies
- Protection contre les boucles infinies dans l'analyse

---

## 📝 Notes de Migration

### De V01 à V02

**Compatibilité** :
- Les fonctionnalités de base (montage/démontage) sont identiques
- Le TreeMap a été retiré au profit de l'explorateur
- L'arborescence a été remplacée par l'explorateur

**Nouvelles dépendances** :
```bash
pip3 install psutil  # Nouveau pour V02
```

**Recommandations** :
- V02 est recommandée pour une utilisation quotidienne
- V01 reste utile pour la visualisation TreeMap
- Les deux versions peuvent coexister

---

**DiskManager V02 - Décembre 2025**
