# -*- mode: python -*-
a = Analysis(['discopy.py'],
             pathex=['D:\\f\\work\\discopy\\Lib\\site-packages', 'D:\\f\\work\\discopy\\discopy'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
a.datas.append(('cacert.pem', '..\\Lib\\site-packages\\requests\\cacert.pem', 'DATA'))
icon_tree = Tree('D:\\f\\work\\discopy\\discopy\\icons', prefix='icons')
thumb_tree = Tree('D:\\f\\work\\discopy\\discopy\\thumbs', prefix='thumbs')
images_tree = Tree('D:\\f\\work\\discopy\\discopy\\images', prefix='images')
settings_tree = Tree('D:\\f\\work\\discopy\\discopy\\settings', prefix='settings')
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          icon_tree,
          thumb_tree,
          images_tree,
          settings_tree,
          name='discopy.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          workpath='D:\\f\\work',
          icon='D:\\f\\work\\discopy\\discopy\\icons\\discopy.ico')

