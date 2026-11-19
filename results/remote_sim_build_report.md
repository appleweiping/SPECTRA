# ngspice/Xyce serial build report

Host: autodl-container-ea9346a03f-a39946f1
Build root: /root/autodl-tmp/sim-build

## ngspice 44.2

- Official source URL: https://git.code.sf.net/p/ngspice/ngspice
- Source tag: ngspice-44.2
- Source commit: 80d22fc802557f8068d83637be905e1536e1c2a4
- Configure: `../ngspice-44.2-src/configure --prefix=/root/autodl-tmp/sim-build/ngspice-44.2-install --with-x --disable-debug`
- Build: `make -j$(nproc)`
- Install: `make install`
- Version: `ngspice-44.2`
- Binary: `/root/autodl-tmp/sim-build/ngspice-44.2-install/bin/ngspice`
- Binary SHA256: `8bd71b6fcdf47033623a2e7eaf38f97b657031df27d400f486b6928e9bc25fe4`
- Smoke: `/root/autodl-tmp/sim-build/ngspice44-smoke.cir`, batch run exited 0, 1008 data rows
- Smoke output SHA256: `9a77dd97be1aae09991e7556586437393c3581fd3624b7963d62f9b79255ed2e`
- Logs: `ngspice44-autogen.log`, `ngspice44-configure.log`, `ngspice44-make.log`, `ngspice44-install.log`

## Xyce 7.10 serial

- Official source URL: https://github.com/Xyce/Xyce.git
- Source describe/tag: Release-7.10.0
- Source commit: a592a42ae7472151d1c8e3bca0ca62d27476f2f3
- Trilinos source branch: trilinos-release-14-4-branch
- Trilinos source commit: 975307431d60d0859ebaa27c9169cbb1d4287513
- SuiteSparse source tag/commit: v7.8.3 / d3c4926d2c47fd6ae558e898bfc072ade210a2a1
- CMake: official 3.29.6 Linux x86_64, tarball SHA256 28fef61e64840b784da6db35218fd3ae179ff8bf0be1c8a9d075d6185a0e4fdc
- Xyce configure: `cmake-3.29.6 -S /root/autodl-tmp/Xyce -B /root/autodl-tmp/sim-build/xyce-7.10-serial-build -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/root/autodl-tmp/sim-build/xyce-7.10-serial-install -D Trilinos_ROOT=/root/autodl-tmp/sim-build/trilinos-14.4-serial-install`
- Build: `cmake-3.29.6 --build /root/autodl-tmp/sim-build/xyce-7.10-serial-build -j32`
- Install: `cmake-3.29.6 --build /root/autodl-tmp/sim-build/xyce-7.10-serial-build --target install -j32`
- Version: `Xyce Release 7.10.0-opensource`
- Binary: `/root/autodl-tmp/sim-build/xyce-7.10-serial-install/bin/Xyce`
- Binary SHA256: `5abf2b7d1dba7c582c37dd64a3773bebf8e76402d7e4898057016965f8cfae79`
- Smoke: `/root/autodl-tmp/sim-build/xyce-smoke.cir`, exit 0, 17 successful steps, 0 failed steps
- Smoke log SHA256: `d3cf0a4c670d6a3fd06c15bbfc364d5f0d615e46e54684f4bdfc2b4800859118`
- Smoke output SHA256: `aaebadfbe608edabcd49915fbd3491633ea63e5ef2bf4e61228744b5006efb93`
- Configure/build/install log SHA256: `2f809ead9797b3a7699666f10128e65d2221b7ca1ea89454aeedb94cf747bb30`, `fcb8b23dc9ca8e4c41879a2e04d01dac9aeaba0734f33070dde265a629112680`, `33af5dba545a94199c62c8b4dcb27e74cc34c52af312176d6e7dc1be7b8d87f9`
- Configuration: MPI disabled for serial. BLAS/LAPACK, AMD, KLU, KLU2, Basker, Amesos2, Stokhos and ROL detected. FFTW unavailable, FFT capability disabled.

## Known failed attempt

- System CMake was 3.22.1. Xyce 7.10/Trilinos 14.4 configure requires CMake >= 3.23. Replaced only the selected build tool with official CMake 3.29.6 under `sim-build/toolchain`; system packages were not modified.

## Environment helper

- Source `/root/autodl-tmp/sim-build/env.sh` to prepend Xyce, ngspice and CMake 3.29.6 to `PATH` and set `SIM_BUILD_ROOT`, `NGSPICE_ROOT`, `XYCE_ROOT`, `TRILINOS_ROOT`.
- Helper SHA256: `4c642ab8955ced81bb21f480e4e68b03a2d6bb90da1f67c1fbbff3943cdad378`.
