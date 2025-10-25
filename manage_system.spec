# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['app.py'],
    pathex=[r'D:\Manage_system\manage_system'],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('templates', 'templates'),
        ('PictureCode', 'PictureCode'),
        ('shixi_uploads', 'shixi_uploads'),
        ('uploads', 'uploads'),
        (r"C:\Users\25129\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.8_qbz5n2kfra8p0\LocalCache\local-packages\Python38\site-packages\cpca\resources", 'cpca/resources'),

        ('settings.py', '.'),
        ('form.py', '.'),
        ('words.txt', '.'),
        ('stopwords.txt', '.'),
        ('package-lock.json', '.'),
        ('result.json', '.'),
        ('SimHei.ttf', '.'),
        ('model.py', '.'),
        ('intern_management.sql', '.'),
    ],
    hiddenimports=[
        'cpca.resources',
        'wordcloud'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='manage_system',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
