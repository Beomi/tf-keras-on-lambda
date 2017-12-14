#!/usr/bin/env bash
dev_install () {
    yum -y update
    yum -y upgrade
    yum install -y \
    wget \
    gcc \
    gcc-c++ \
    python36-devel \
    python36-virtualenv \
    python36-pip \
    findutils \
    zlib-devel \
    zip
}

pip_rasterio () {
    cd /home/
    rm -rf env
    python3 -m virtualenv env --python=python3
    source env/bin/activate
    text="
    [global]
    index-url=http://ftp.daumkakao.com/pypi/simple
    trusted-host=ftp.daumkakao.com
    "
    echo "$text" > $VIRTUAL_ENV/pip.conf
    echo "UNDER: pip.conf ==="
    cat $VIRTUAL_ENV/pip.conf
    pip install -U pip wheel
    # pip install -r /outputs/requirements.txt
    pip install --use-wheel "h5py==2.6.0"
    pip install "pillow==4.0.0"
    pip install protobuf html5lib bleach --no-deps
    pip install --use-wheel tensorflow --no-deps
    deactivate
}


gather_pack () {
    # packing
    cd /home/
    source env/bin/activate

    rm -rf lambdapack
    mkdir lambdapack
    cd lambdapack

    cp -R /home/env/lib/python3.6/site-packages/* .
    cp -R /home/env/lib64/python3.6/site-packages/* .
    cp /outputs/squeezenet.py /home/lambdapack/squeezenet.py
    cp /outputs/index.py /home/lambdapack/index.py
    echo "original size $(du -sh /home/lambdapack | cut -f1)"

    # cleaning libs
    rm -rf external

    # cleaning
    find -name "*.so" | xargs strip
    find -name "*.so.*" | xargs strip
    rm -r pip
    rm -r pip-*
    rm -r wheel
    rm -r wheel-*
    rm easy_install.py
    find . -name \*.pyc -delete
    # find . -name \*.txt -delete
    echo "stripped size $(du -sh /home/lambdapack | cut -f1)"

    # compressing
    zip -FS -r1 /outputs/pack.zip * > /dev/null
    echo "compressed size $(du -sh /outputs/pack.zip | cut -f1)"
}

main () {
    dev_install
    pip_rasterio
    gather_pack
}

main
