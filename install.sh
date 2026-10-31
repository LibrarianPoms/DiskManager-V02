#!/bin/bash
# Script d'installation pour Gestionnaire de Disques V02

echo "=========================================="
echo "Installation Gestionnaire de Disques V02"
echo "=========================================="
echo ""

# Vérifier si Python3 est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    echo "Installation de Python3..."
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

echo "✅ Python3 installé: $(python3 --version)"
echo ""

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "Installation de pip3..."
    sudo apt install -y python3-pip
fi

echo "✅ pip3 installé"
echo ""

# Installer les dépendances système
echo "📦 Installation des dépendances système..."
sudo apt update
sudo apt install -y ntfs-3g python3-pyqt5

echo ""
echo "📦 Installation des dépendances Python..."

# Installer les dépendances Python
pip3 install --user PyQt5 matplotlib psutil

echo ""
echo "🔧 Configuration des permissions..."

# Rendre le script exécutable
chmod +x disk_manager_v02.py

echo ""
echo "✅ Installation terminée !"
echo ""
echo "=========================================="
echo "Pour lancer l'application :"
echo "  python3 disk_manager_v02.py"
echo "ou"
echo "  ./disk_manager_v02.py"
echo "=========================================="
