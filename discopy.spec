# -*- mode: python -*-
a = Analysis(['discopy.py'],
             pathex=['/home/antx/wrk/py/discopy/lib/python2.7/site-packages', '/home/antx/wrk/py/discopy/discopy/discopy'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
a.datas.append(('cacert.pem', '../../lib/python2.7/site-packages/requests/cacert.pem', 'DATA'))
icon_tree = Tree('/home/antx/wrk/py/discopy/discopy/discopy/icons', prefix='icons')
thumb_tree = Tree('/home/antx/wrk/py/discopy/discopy/discopy/thumbs', prefix='thumbs')
settings_tree = Tree('/home/antx/wrk/py/discopy/discopy/discopy/settings', prefix='settings')
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          icon_tree,
          thumb_tree,
          settings_tree,
          name='discopy',
          debug=True,
          strip=None,
          upx=False,
          console=True )

