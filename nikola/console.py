from __future__ import print_function, unicode_literals

from nikola import Nikola
import conf
SITE = Nikola(**conf.__dict__)
SITE.scan_posts()
print("You can now access your configuration as conf and your site engine as SITE")
