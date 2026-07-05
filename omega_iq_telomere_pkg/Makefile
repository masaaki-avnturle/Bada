# omega_iq_telomere_pkg — Bada 赤外線IQ・テロメア分裂測定アプリ
RUBY ?= ruby

.PHONY: all run apk test clean

all: apk

# run the Bada app directly on the runtime
run:
	$(RUBY) bin/run_iq app/main.bada

# assemble the APK-format package (dist/bada_iq.apk) and launch it
apk:
	sh run.sh

# build the apk only, without launching
package:
	sh build_apk.sh

test:
	$(RUBY) test/test_iq.rb

clean:
	rm -rf dist/run dist/bada_iq.apk META-INF/MANIFEST.MF dist/_val.txt
