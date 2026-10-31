#!/usr/bin/env python3
"""
Gestionnaire de Disques V02 avec Explorateur de Fichiers Avancé
Permet de monter/démonter des disques, visualiser leur utilisation et explorer les fichiers
"""

import sys
import os
import subprocess
import json
import pwd
import grp
import stat
import psutil
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QComboBox,
    QMessageBox, QProgressBar, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QSplitter, QGroupBox, QRadioButton, QButtonGroup, QTextEdit, QLineEdit,
    QHeaderView, QMenu, QAction, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QFileInfo
from PyQt5.QtGui import QIcon, QFont, QColor, QCursor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DiskScanner(QThread):
    """Thread pour scanner les disques sans bloquer l'interface"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            result = subprocess.run(
                ['lsblk', '-npo', 'NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT,UUID', '-J'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            disks = []
            
            for device in data.get('blockdevices', []):
                self._process_device(device, disks)
            
            self.finished.emit(disks)
        except Exception as e:
            self.error.emit(f"Erreur lors du scan: {str(e)}")
    
    def _process_device(self, device, disks, parent_name=None):
        """Traiter récursivement les périphériques et leurs partitions"""
        name = device.get('name', '')
        
        if 'loop' in name:
            return
        
        fstype = device.get('fstype', '')
        mountpoint = device.get('mountpoint', '')
        
        if fstype and fstype != 'swap':
            if mountpoint not in ['/', '/boot/efi', '/home']:
                disk_info = {
                    'name': name,
                    'size': device.get('size', ''),
                    'fstype': fstype,
                    'label': device.get('label', ''),
                    'mountpoint': mountpoint,
                    'uuid': device.get('uuid', ''),
                    'mounted': bool(mountpoint)
                }
                disks.append(disk_info)
        
        for child in device.get('children', []):
            self._process_device(child, disks, name)


class DiskUsageAnalyzer(QThread):
    """Thread pour analyser l'utilisation du disque"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.should_stop = False
    
    def run(self):
        try:
            self.progress.emit(0, "Analyse en cours...")
            result = self._analyze_directory(self.path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"Erreur d'analyse: {str(e)}")
    
    def stop(self):
        self.should_stop = True
    
    def _analyze_directory(self, path, max_depth=3, current_depth=0):
        """Analyser récursivement un répertoire"""
        if self.should_stop or current_depth > max_depth:
            return None
        
        try:
            total_size = 0
            children = []
            
            with os.scandir(path) as entries:
                for entry in entries:
                    if self.should_stop:
                        break
                    
                    try:
                        if entry.is_file(follow_symlinks=False):
                            size = entry.stat().st_size
                            total_size += size
                            children.append({
                                'name': entry.name,
                                'path': entry.path,
                                'size': size,
                                'type': 'file',
                                'children': []
                            })
                        elif entry.is_dir(follow_symlinks=False):
                            subdir_data = self._analyze_directory(
                                entry.path, max_depth, current_depth + 1
                            )
                            if subdir_data:
                                total_size += subdir_data['size']
                                children.append(subdir_data)
                    except (PermissionError, OSError):
                        continue
            
            return {
                'name': os.path.basename(path) or path,
                'path': path,
                'size': total_size,
                'type': 'directory',
                'children': sorted(children, key=lambda x: x['size'], reverse=True)
            }
        except Exception:
            return None


class FileExplorerWidget(QWidget):
    """Widget explorateur de fichiers avancé"""
    
    def __init__(self):
        super().__init__()
        self.current_path = os.path.expanduser('~')
        self.init_ui()
        self.load_directory(self.current_path)
    
    def init_ui(self):
        """Initialiser l'interface de l'explorateur"""
        layout = QVBoxLayout()
        
        # Barre de navigation
        nav_layout = QHBoxLayout()
        
        self.back_btn = QPushButton('⬅ Retour')
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.home_btn = QPushButton('🏠 Accueil')
        self.home_btn.clicked.connect(self.go_home)
        self.home_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        
        self.up_btn = QPushButton('⬆ Parent')
        self.up_btn.clicked.connect(self.go_up)
        self.up_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #2196F3;
                border-radius: 4px;
                background-color: #f0f0f0;
                font-weight: bold;
            }
        """)
        
        self.refresh_btn = QPushButton('🔄 Actualiser')
        self.refresh_btn.clicked.connect(self.refresh)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.up_btn)
        nav_layout.addWidget(self.home_btn)
        nav_layout.addWidget(self.path_edit, 1)
        nav_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(nav_layout)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        search_label = QLabel('🔍 Rechercher:')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Filtrer les fichiers...')
        self.search_edit.textChanged.connect(self.filter_files)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Table des fichiers
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(9)
        self.file_table.setHorizontalHeaderLabels([
            'Nom', 'Taille', 'Type', 'Propriétaire', 'Groupe', 
            'Permissions', 'Modifié', 'Créé', 'Accédé'
        ])
        
        # Configurer les colonnes
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 9):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SingleSelection)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSortingEnabled(True)
        self.file_table.doubleClicked.connect(self.on_item_double_clicked)
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.file_table)
        
        # Barre d'information
        self.info_label = QLabel('')
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #e3f2fd;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
        
        # Historique de navigation
        self.history = []
        self.history_index = -1
    
    def load_directory(self, path):
        """Charger le contenu d'un répertoire"""
        try:
            self.current_path = path
            self.path_edit.setText(path)
            self.file_table.setRowCount(0)
            self.file_table.setSortingEnabled(False)
            
            # Lister les fichiers
            entries = []
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        try:
                            stat_info = entry.stat(follow_symlinks=False)
                            entries.append((entry, stat_info))
                        except (PermissionError, OSError):
                            continue
            except PermissionError:
                QMessageBox.warning(self, 'Accès refusé', f'Impossible d\'accéder à {path}')
                return
            
            # Trier: dossiers d'abord, puis fichiers
            entries.sort(key=lambda x: (not x[0].is_dir(), x[0].name.lower()))
            
            # Remplir la table
            for entry, stat_info in entries:
                self.add_file_row(entry, stat_info)
            
            self.file_table.setSortingEnabled(True)
            
            # Mettre à jour les infos
            num_files = sum(1 for e, _ in entries if not e.is_dir())
            num_dirs = sum(1 for e, _ in entries if e.is_dir())
            self.info_label.setText(
                f'📁 {num_dirs} dossier(s) • 📄 {num_files} fichier(s) • 📍 {path}'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors du chargement: {str(e)}')
    
    def add_file_row(self, entry, stat_info):
        """Ajouter une ligne pour un fichier/dossier"""
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        # Nom avec icône
        name = entry.name
        if entry.is_dir():
            icon = '📁'
            file_type = 'Dossier'
        elif entry.is_symlink():
            icon = '🔗'
            file_type = 'Lien symbolique'
        else:
            icon = self.get_file_icon(name)
            file_type = self.get_file_type(name)
        
        name_item = QTableWidgetItem(f'{icon} {name}')
        name_item.setData(Qt.UserRole, entry.path)
        if entry.is_dir():
            name_item.setForeground(QColor('#1976d2'))
            name_item.setFont(QFont('', -1, QFont.Bold))
        self.file_table.setItem(row, 0, name_item)
        
        # Taille
        if entry.is_file():
            size = self.format_size(stat_info.st_size)
        else:
            size = '-'
        self.file_table.setItem(row, 1, QTableWidgetItem(size))
        
        # Type
        self.file_table.setItem(row, 2, QTableWidgetItem(file_type))
        
        # Propriétaire
        try:
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
        except KeyError:
            owner = str(stat_info.st_uid)
        self.file_table.setItem(row, 3, QTableWidgetItem(owner))
        
        # Groupe
        try:
            group = grp.getgrgid(stat_info.st_gid).gr_name
        except KeyError:
            group = str(stat_info.st_gid)
        self.file_table.setItem(row, 4, QTableWidgetItem(group))
        
        # Permissions
        perms = self.format_permissions(stat_info.st_mode)
        perm_item = QTableWidgetItem(perms)
        if perms.startswith('d'):
            perm_item.setForeground(QColor('#1976d2'))
        self.file_table.setItem(row, 5, perm_item)
        
        # Date de modification
        mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        self.file_table.setItem(row, 6, QTableWidgetItem(mtime))
        
        # Date de création (ctime sur Linux = changement de métadonnées)
        ctime = datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        self.file_table.setItem(row, 7, QTableWidgetItem(ctime))
        
        # Date d'accès
        atime = datetime.fromtimestamp(stat_info.st_atime).strftime('%Y-%m-%d %H:%M:%S')
        self.file_table.setItem(row, 8, QTableWidgetItem(atime))
    
    def get_file_icon(self, filename):
        """Obtenir l'icône selon l'extension"""
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.py': '🐍', '.txt': '📝', '.pdf': '📕', '.doc': '📘', '.docx': '📘',
            '.xls': '📊', '.xlsx': '📊', '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️',
            '.gif': '🖼️', '.mp3': '🎵', '.mp4': '🎬', '.avi': '🎬', '.zip': '📦',
            '.tar': '📦', '.gz': '📦', '.sh': '⚙️', '.exe': '⚙️', '.html': '🌐',
            '.css': '🎨', '.js': '📜', '.json': '📋', '.xml': '📋', '.md': '📄',
            '.cpp': '⚡', '.c': '⚡', '.h': '⚡', '.java': '☕', '.class': '☕'
        }
        return icons.get(ext, '📄')
    
    def get_file_type(self, filename):
        """Obtenir le type de fichier"""
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            return 'Fichier'
        return f'Fichier {ext[1:].upper()}'
    
    def format_size(self, size):
        """Formater la taille"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def format_permissions(self, mode):
        """Formater les permissions en format rwx"""
        perms = ''
        
        # Type
        if stat.S_ISDIR(mode):
            perms = 'd'
        elif stat.S_ISLNK(mode):
            perms = 'l'
        else:
            perms = '-'
        
        # Propriétaire
        perms += 'r' if mode & stat.S_IRUSR else '-'
        perms += 'w' if mode & stat.S_IWUSR else '-'
        perms += 'x' if mode & stat.S_IXUSR else '-'
        
        # Groupe
        perms += 'r' if mode & stat.S_IRGRP else '-'
        perms += 'w' if mode & stat.S_IWGRP else '-'
        perms += 'x' if mode & stat.S_IXGRP else '-'
        
        # Autres
        perms += 'r' if mode & stat.S_IROTH else '-'
        perms += 'w' if mode & stat.S_IWOTH else '-'
        perms += 'x' if mode & stat.S_IXOTH else '-'
        
        return perms
    
    def on_item_double_clicked(self, index):
        """Gérer le double-clic sur un élément"""
        row = index.row()
        path = self.file_table.item(row, 0).data(Qt.UserRole)
        
        if os.path.isdir(path):
            # Ajouter à l'historique
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            self.history.append(self.current_path)
            self.history_index = len(self.history) - 1
            
            self.load_directory(path)
        else:
            # Afficher les infos du fichier
            self.show_file_info(path)
    
    def show_file_info(self, path):
        """Afficher les informations détaillées d'un fichier"""
        try:
            stat_info = os.stat(path)
            info = f"""
📄 Fichier: {os.path.basename(path)}
📍 Chemin: {path}
📏 Taille: {self.format_size(stat_info.st_size)}
👤 Propriétaire: {pwd.getpwuid(stat_info.st_uid).pw_name}
👥 Groupe: {grp.getgrgid(stat_info.st_gid).gr_name}
🔒 Permissions: {self.format_permissions(stat_info.st_mode)}
📅 Modifié: {datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}
📅 Créé: {datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}
📅 Accédé: {datetime.fromtimestamp(stat_info.st_atime).strftime('%Y-%m-%d %H:%M:%S')}
            """
            QMessageBox.information(self, 'Informations du fichier', info.strip())
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur: {str(e)}')
    
    def show_context_menu(self, position):
        """Afficher le menu contextuel"""
        menu = QMenu()
        
        open_action = QAction('📂 Ouvrir', self)
        open_action.triggered.connect(self.open_selected)
        menu.addAction(open_action)
        
        info_action = QAction('ℹ️ Propriétés', self)
        info_action.triggered.connect(self.show_selected_info)
        menu.addAction(info_action)
        
        menu.addSeparator()
        
        copy_path_action = QAction('📋 Copier le chemin', self)
        copy_path_action.triggered.connect(self.copy_path)
        menu.addAction(copy_path_action)
        
        menu.exec_(self.file_table.viewport().mapToGlobal(position))
    
    def open_selected(self):
        """Ouvrir l'élément sélectionné"""
        current_row = self.file_table.currentRow()
        if current_row >= 0:
            index = self.file_table.model().index(current_row, 0)
            self.on_item_double_clicked(index)
    
    def show_selected_info(self):
        """Afficher les infos de l'élément sélectionné"""
        current_row = self.file_table.currentRow()
        if current_row >= 0:
            path = self.file_table.item(current_row, 0).data(Qt.UserRole)
            self.show_file_info(path)
    
    def copy_path(self):
        """Copier le chemin dans le presse-papier"""
        current_row = self.file_table.currentRow()
        if current_row >= 0:
            path = self.file_table.item(current_row, 0).data(Qt.UserRole)
            QApplication.clipboard().setText(path)
            self.info_label.setText(f'📋 Chemin copié: {path}')
    
    def filter_files(self, text):
        """Filtrer les fichiers selon le texte de recherche"""
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                self.file_table.setRowHidden(row, text.lower() not in item.text().lower())
    
    def go_back(self):
        """Retour dans l'historique"""
        if self.history_index > 0:
            self.history_index -= 1
            self.load_directory(self.history[self.history_index])
    
    def go_up(self):
        """Aller au dossier parent"""
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path:
            self.load_directory(parent)
    
    def go_home(self):
        """Aller au dossier personnel"""
        self.load_directory(os.path.expanduser('~'))
    
    def refresh(self):
        """Actualiser le répertoire courant"""
        self.load_directory(self.current_path)


class ProcessViewerWidget(QWidget):
    """Widget pour visualiser les processus en cours"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_processes()
        
        # Timer pour actualiser automatiquement
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_processes)
        self.timer.start(3000)  # Actualiser toutes les 3 secondes
    
    def init_ui(self):
        """Initialiser l'interface"""
        layout = QVBoxLayout()
        
        # Barre d'outils
        toolbar = QHBoxLayout()
        
        self.refresh_btn = QPushButton('🔄 Actualiser')
        self.refresh_btn.clicked.connect(self.load_processes)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.auto_refresh_label = QLabel('🔄 Actualisation automatique: 3s')
        self.auto_refresh_label.setStyleSheet('font-weight: bold; color: #4CAF50;')
        
        # Filtre
        filter_label = QLabel('🔍 Filtrer:')
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText('Nom du processus...')
        self.filter_edit.textChanged.connect(self.filter_processes)
        
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.auto_refresh_label)
        toolbar.addStretch()
        toolbar.addWidget(filter_label)
        toolbar.addWidget(self.filter_edit)
        
        layout.addLayout(toolbar)
        
        # Table des processus
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            'PID', 'Nom', 'Utilisateur', 'CPU %', 'Mémoire %', 
            'Mémoire (MB)', 'État', 'Commande'
        ])
        
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setSortingEnabled(True)
        self.process_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_process_menu)
        
        layout.addWidget(self.process_table)
        
        # Informations système
        self.sys_info_label = QLabel('')
        self.sys_info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #e3f2fd;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.sys_info_label)
        
        self.setLayout(layout)
    
    def load_processes(self):
        """Charger la liste des processus"""
        try:
            self.process_table.setSortingEnabled(False)
            self.process_table.setRowCount(0)
            
            # Informations système
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                            'memory_percent', 'memory_info', 'status', 'cmdline']):
                try:
                    pinfo = proc.info
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Trier par utilisation CPU
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            # Remplir la table
            for pinfo in processes[:200]:  # Limiter à 200 processus
                self.add_process_row(pinfo)
            
            self.process_table.setSortingEnabled(True)
            
            # Mettre à jour les infos système
            self.sys_info_label.setText(
                f'💻 CPU: {cpu_percent:.1f}% • '
                f'🧠 Mémoire: {mem.percent:.1f}% ({self.format_size(mem.used)}/{self.format_size(mem.total)}) • '
                f'📊 {len(processes)} processus'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors du chargement: {str(e)}')
    
    def add_process_row(self, pinfo):
        """Ajouter une ligne pour un processus"""
        row = self.process_table.rowCount()
        self.process_table.insertRow(row)
        
        # PID
        pid_item = QTableWidgetItem(str(pinfo.get('pid', '')))
        self.process_table.setItem(row, 0, pid_item)
        
        # Nom
        name = pinfo.get('name', 'N/A')
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, pinfo.get('pid'))
        self.process_table.setItem(row, 1, name_item)
        
        # Utilisateur
        username = pinfo.get('username', 'N/A')
        self.process_table.setItem(row, 2, QTableWidgetItem(username))
        
        # CPU %
        cpu = pinfo.get('cpu_percent', 0)
        cpu_item = QTableWidgetItem(f'{cpu:.1f}')
        if cpu > 50:
            cpu_item.setForeground(QColor('red'))
        elif cpu > 20:
            cpu_item.setForeground(QColor('orange'))
        self.process_table.setItem(row, 3, cpu_item)
        
        # Mémoire %
        mem_percent = pinfo.get('memory_percent', 0)
        mem_item = QTableWidgetItem(f'{mem_percent:.1f}')
        if mem_percent > 10:
            mem_item.setForeground(QColor('red'))
        elif mem_percent > 5:
            mem_item.setForeground(QColor('orange'))
        self.process_table.setItem(row, 4, mem_item)
        
        # Mémoire (MB)
        mem_info = pinfo.get('memory_info')
        if mem_info:
            mem_mb = mem_info.rss / (1024 * 1024)
            self.process_table.setItem(row, 5, QTableWidgetItem(f'{mem_mb:.1f}'))
        else:
            self.process_table.setItem(row, 5, QTableWidgetItem('N/A'))
        
        # État
        status = pinfo.get('status', 'N/A')
        status_item = QTableWidgetItem(status)
        if status == 'running':
            status_item.setForeground(QColor('green'))
        elif status == 'sleeping':
            status_item.setForeground(QColor('blue'))
        self.process_table.setItem(row, 6, status_item)
        
        # Commande
        cmdline = pinfo.get('cmdline', [])
        if cmdline:
            cmd = ' '.join(cmdline)
            if len(cmd) > 100:
                cmd = cmd[:97] + '...'
        else:
            cmd = name
        self.process_table.setItem(row, 7, QTableWidgetItem(cmd))
    
    def format_size(self, size):
        """Formater la taille"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"
    
    def filter_processes(self, text):
        """Filtrer les processus"""
        for row in range(self.process_table.rowCount()):
            item = self.process_table.item(row, 1)
            if item:
                self.process_table.setRowHidden(row, text.lower() not in item.text().lower())
    
    def show_process_menu(self, position):
        """Afficher le menu contextuel"""
        menu = QMenu()
        
        info_action = QAction('ℹ️ Détails', self)
        info_action.triggered.connect(self.show_process_info)
        menu.addAction(info_action)
        
        menu.addSeparator()
        
        kill_action = QAction('❌ Terminer le processus', self)
        kill_action.triggered.connect(self.kill_process)
        menu.addAction(kill_action)
        
        menu.exec_(self.process_table.viewport().mapToGlobal(position))
    
    def show_process_info(self):
        """Afficher les détails d'un processus"""
        current_row = self.process_table.currentRow()
        if current_row >= 0:
            pid = self.process_table.item(current_row, 1).data(Qt.UserRole)
            try:
                proc = psutil.Process(pid)
                info = f"""
🔢 PID: {proc.pid}
📛 Nom: {proc.name()}
👤 Utilisateur: {proc.username()}
💻 CPU: {proc.cpu_percent(interval=0.1):.1f}%
🧠 Mémoire: {proc.memory_percent():.2f}%
📊 État: {proc.status()}
⏰ Créé: {datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S')}
📂 Répertoire: {proc.cwd()}
🔧 Commande: {' '.join(proc.cmdline())}
                """
                QMessageBox.information(self, f'Processus {pid}', info.strip())
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                QMessageBox.warning(self, 'Erreur', f'Impossible d\'accéder au processus: {str(e)}')
    
    def kill_process(self):
        """Terminer un processus"""
        current_row = self.process_table.currentRow()
        if current_row >= 0:
            pid = self.process_table.item(current_row, 1).data(Qt.UserRole)
            name = self.process_table.item(current_row, 1).text()
            
            reply = QMessageBox.question(
                self, 'Confirmation',
                f'Voulez-vous vraiment terminer le processus "{name}" (PID: {pid}) ?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    QMessageBox.information(self, 'Succès', f'Processus {pid} terminé')
                    self.load_processes()
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    QMessageBox.critical(self, 'Erreur', f'Erreur: {str(e)}')


class PieChartWidget(QWidget):
    """Widget pour afficher un graphique en camembert"""
    
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def plot_disk_usage(self, data, path):
        """Afficher l'utilisation du disque en camembert"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not data or not data.get('children'):
            ax.text(0.5, 0.5, 'Aucune donnée à afficher',
                   ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return
        
        children = [child for child in data['children'][:10] if child['size'] > 0]
        other_size = sum(child['size'] for child in data['children'][10:] if child['size'] > 0)
        
        sizes = [child['size'] for child in children]
        labels = [self._format_label(child) for child in children]
        
        if other_size > 0:
            sizes.append(other_size)
            labels.append(f'Autres ({self._format_size(other_size)})')
        
        if not sizes or sum(sizes) == 0:
            ax.text(0.5, 0.5, 'Aucune donnée valide à afficher',
                   ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return
        
        colors = plt.cm.Set3(range(len(sizes)))
        
        try:
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct=lambda pct: f'{pct:.1f}%' if pct > 3 else '',
                startangle=90,
                colors=colors
            )
        except (ValueError, ZeroDivisionError) as e:
            ax.text(0.5, 0.5, f'Erreur lors de la génération du graphique\n{str(e)[:100]}',
                   ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return
        
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)
            autotext.set_weight('bold')
        
        ax.set_title(f'Utilisation du disque: {path}', fontsize=12, weight='bold')
        ax.axis('equal')
        
        self.canvas.draw()
    
    def _format_label(self, item):
        """Formater le label avec nom et taille"""
        name = item['name']
        if len(name) > 20:
            name = name[:17] + '...'
        size = self._format_size(item['size'])
        return f'{name}\n({size})'
    
    def _format_size(self, size):
        """Formater la taille en unités lisibles"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


class DiskManagerGUI(QMainWindow):
    """Interface principale de gestion des disques V02"""
    
    def __init__(self):
        super().__init__()
        self.current_disk = None
        self.analyzer_thread = None
        self.init_ui()
        self.scan_disks()
    
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        self.setWindowTitle('Gestionnaire de Disques V02 - Explorateur Avancé')
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Titre
        title = QLabel('🖴 Gestionnaire de Disques V02 - Explorateur Avancé')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Splitter principal
        splitter = QSplitter(Qt.Vertical)
        
        # === PARTIE SUPÉRIEURE: Gestion des disques ===
        disk_widget = QWidget()
        disk_layout = QVBoxLayout()
        disk_widget.setLayout(disk_layout)
        
        refresh_btn = QPushButton('🔄 Rafraîchir la liste des disques')
        refresh_btn.clicked.connect(self.scan_disks)
        disk_layout.addWidget(refresh_btn)
        
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(7)
        self.disk_table.setHorizontalHeaderLabels([
            'Périphérique', 'Taille', 'Type', 'Label', 'Point de montage', 'État', 'Actions'
        ])
        self.disk_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.disk_table.setSelectionMode(QTableWidget.SingleSelection)
        disk_layout.addWidget(self.disk_table)
        
        mount_options_group = QGroupBox('Options de montage')
        mount_options_layout = QHBoxLayout()
        
        self.mount_mode_group = QButtonGroup()
        self.rb_readonly = QRadioButton('Lecture seule')
        self.rb_readwrite = QRadioButton('Lecture-écriture')
        self.rb_readwrite.setChecked(True)
        
        self.mount_mode_group.addButton(self.rb_readonly)
        self.mount_mode_group.addButton(self.rb_readwrite)
        
        mount_options_layout.addWidget(self.rb_readonly)
        mount_options_layout.addWidget(self.rb_readwrite)
        mount_options_layout.addStretch()
        
        mount_options_group.setLayout(mount_options_layout)
        disk_layout.addWidget(mount_options_group)
        
        splitter.addWidget(disk_widget)
        
        # === PARTIE INFÉRIEURE: Onglets ===
        tabs = QTabWidget()
        
        # Onglet 1: Explorateur de fichiers
        self.file_explorer = FileExplorerWidget()
        tabs.addTab(self.file_explorer, '📂 Explorateur de Fichiers')
        
        # Onglet 2: Processus
        self.process_viewer = ProcessViewerWidget()
        tabs.addTab(self.process_viewer, '⚙️ Processus')
        
        # Onglet 3: Graphique circulaire
        self.pie_chart = PieChartWidget()
        tabs.addTab(self.pie_chart, '📊 Graphique circulaire')
        
        # Onglet 4: Logs
        log_widget = QWidget()
        log_layout = QVBoxLayout()
        log_widget.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        tabs.addTab(log_widget, '📝 Logs')
        
        splitter.addWidget(tabs)
        
        splitter.setSizes([300, 600])
        
        main_layout.addWidget(splitter)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Barre de statut
        self.status_label = QLabel('Prêt')
        main_layout.addWidget(self.status_label)
        
        self.log('Application V02 démarrée')
    
    def log(self, message):
        """Ajouter un message aux logs"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def scan_disks(self):
        """Scanner les disques disponibles"""
        self.status_label.setText('Scan des disques en cours...')
        self.log('Scan des disques...')
        
        self.scanner = DiskScanner()
        self.scanner.finished.connect(self.on_scan_finished)
        self.scanner.error.connect(self.on_scan_error)
        self.scanner.start()
    
    def on_scan_finished(self, disks):
        """Callback quand le scan est terminé"""
        self.disk_table.setRowCount(0)
        
        for disk in disks:
            row = self.disk_table.rowCount()
            self.disk_table.insertRow(row)
            
            self.disk_table.setItem(row, 0, QTableWidgetItem(disk['name']))
            self.disk_table.setItem(row, 1, QTableWidgetItem(disk['size']))
            self.disk_table.setItem(row, 2, QTableWidgetItem(disk['fstype']))
            
            label = disk['label'] if disk['label'] else '-'
            self.disk_table.setItem(row, 3, QTableWidgetItem(label))
            
            mountpoint = disk['mountpoint'] if disk['mountpoint'] else '-'
            self.disk_table.setItem(row, 4, QTableWidgetItem(mountpoint))
            
            status_item = QTableWidgetItem('✓ Monté' if disk['mounted'] else '✗ Non monté')
            if disk['mounted']:
                status_item.setForeground(QColor('green'))
            else:
                status_item.setForeground(QColor('red'))
            self.disk_table.setItem(row, 5, status_item)
            
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            if disk['mounted']:
                unmount_btn = QPushButton('Démonter')
                unmount_btn.clicked.connect(
                    lambda checked, d=disk: self.unmount_disk(d)
                )
                action_layout.addWidget(unmount_btn)
                
                analyze_btn = QPushButton('Analyser')
                analyze_btn.clicked.connect(
                    lambda checked, d=disk: self.analyze_disk(d)
                )
                action_layout.addWidget(analyze_btn)
                
                explore_btn = QPushButton('Explorer')
                explore_btn.clicked.connect(
                    lambda checked, d=disk: self.explore_disk(d)
                )
                action_layout.addWidget(explore_btn)
            else:
                mount_btn = QPushButton('Monter')
                mount_btn.clicked.connect(
                    lambda checked, d=disk: self.mount_disk(d)
                )
                action_layout.addWidget(mount_btn)
            
            action_widget.setLayout(action_layout)
            self.disk_table.setCellWidget(row, 6, action_widget)
        
        self.disk_table.resizeColumnsToContents()
        self.status_label.setText(f'{len(disks)} disque(s) détecté(s)')
        self.log(f'{len(disks)} disque(s) détecté(s)')
    
    def on_scan_error(self, error):
        """Callback en cas d'erreur de scan"""
        QMessageBox.critical(self, 'Erreur', error)
        self.status_label.setText('Erreur de scan')
        self.log(f'ERREUR: {error}')
    
    def mount_disk(self, disk):
        """Monter un disque"""
        mode = 'rw' if self.rb_readwrite.isChecked() else 'ro'
        
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f"Monter {disk['name']} en mode {mode} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        self.log(f"Montage de {disk['name']} en mode {mode}...")
        
        try:
            label = disk['label'] if disk['label'] else f"disk_{os.path.basename(disk['name'])}"
            mount_point = f"/media/{os.getenv('USER')}/{label}"
            
            subprocess.run(['sudo', 'mkdir', '-p', mount_point], check=True)
            
            uid = os.getuid()
            gid = os.getgid()
            
            if disk['fstype'] == 'ntfs':
                options = f"{mode},uid={uid},gid={gid},umask=0022"
                subprocess.run([
                    'sudo', 'mount', '-t', 'ntfs-3g', '-o', options,
                    disk['name'], mount_point
                ], check=True)
            else:
                options = f"{mode}"
                subprocess.run([
                    'sudo', 'mount', '-o', options,
                    disk['name'], mount_point
                ], check=True)
            
            QMessageBox.information(
                self,
                'Succès',
                f"Disque monté avec succès sur {mount_point}"
            )
            self.log(f"✓ Disque monté: {mount_point}")
            self.scan_disks()
            
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self,
                'Erreur',
                f"Erreur lors du montage: {e}"
            )
            self.log(f"✗ Erreur de montage: {e}")
    
    def unmount_disk(self, disk):
        """Démonter un disque"""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f"Démonter {disk['name']} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        self.log(f"Démontage de {disk['name']}...")
        
        try:
            subprocess.run(['sudo', 'umount', disk['name']], check=True)
            
            QMessageBox.information(
                self,
                'Succès',
                f"Disque démonté avec succès"
            )
            self.log(f"✓ Disque démonté: {disk['name']}")
            self.scan_disks()
            
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self,
                'Erreur',
                f"Erreur lors du démontage: {e}"
            )
            self.log(f"✗ Erreur de démontage: {e}")
    
    def analyze_disk(self, disk):
        """Analyser l'utilisation d'un disque"""
        if not disk['mountpoint']:
            QMessageBox.warning(
                self,
                'Attention',
                'Le disque doit être monté pour être analysé'
            )
            return
        
        self.current_disk = disk
        self.status_label.setText(f"Analyse de {disk['mountpoint']}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log(f"Analyse de {disk['mountpoint']}...")
        
        self.analyzer_thread = DiskUsageAnalyzer(disk['mountpoint'])
        self.analyzer_thread.finished.connect(self.on_analysis_finished)
        self.analyzer_thread.progress.connect(self.on_analysis_progress)
        self.analyzer_thread.error.connect(self.on_analysis_error)
        self.analyzer_thread.start()
    
    def explore_disk(self, disk):
        """Explorer un disque dans l'explorateur de fichiers"""
        if not disk['mountpoint']:
            QMessageBox.warning(
                self,
                'Attention',
                'Le disque doit être monté pour être exploré'
            )
            return
        
        self.log(f"Exploration de {disk['mountpoint']}...")
        self.file_explorer.load_directory(disk['mountpoint'])
        # Basculer vers l'onglet explorateur
        tabs = self.centralWidget().findChild(QTabWidget)
        if tabs:
            tabs.setCurrentIndex(0)
    
    def on_analysis_finished(self, data):
        """Callback quand l'analyse est terminée"""
        self.progress_bar.setVisible(False)
        self.status_label.setText('Analyse terminée')
        self.log('✓ Analyse terminée')
        
        if data:
            path = self.current_disk['mountpoint']
            self.pie_chart.plot_disk_usage(data, path)
    
    def on_analysis_progress(self, percent, message):
        """Callback pour la progression de l'analyse"""
        self.status_label.setText(message)
    
    def on_analysis_error(self, error):
        """Callback en cas d'erreur d'analyse"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Erreur', error)
        self.status_label.setText('Erreur d\'analyse')
        self.log(f'✗ Erreur d\'analyse: {error}')


def main():
    """Point d'entrée principal"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = DiskManagerGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
