# -*- mode: python -*-
a = Analysis(['../discopy.py'],
             pathex=['/home/grim/wrk/py/discopy_venv/lib/python2.7/site-packages/', '/home/grim/wrk/py/discopy_venv/discopy'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
a.datas.append(('cacert.pem', '../lib/python2.7/site-packages/requests/cacert.pem', 'DATA'))
icon_tree = Tree('/home/grim/wrk/py/discopy_venv/discopy/icons', prefix='icons')
thumb_tree = Tree('/home/grim/wrk/py/discopy_venv/discopy/thumbs', prefix='thumbs')
images_tree = Tree('/home/grim/wrk/py/discopy_venv/discopy/images', prefix='images')
settings_tree = Tree('/home/grim/wrk/py/discopy_venv/discopy/settings', prefix='settings')
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
          name='discopy',
          debug=True,
          strip=None,
          upx=False,
          console=True,
          icon='/home/grim/wrk/py/discopy_venv/discopy/icons/discopy.ico' )
