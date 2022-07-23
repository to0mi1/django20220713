FROM centos:7

RUN yum groupinstall -y "Development Tools"
RUN yum install -y openssl-devel libffi-devel bzip2-devel \
    wget ca-certificates \
    httpd httpd-devel
RUN alternatives --install /usr/local/bin/sqlite3 sqlite3 /usr/sqlite330/bin/sqlite3 1

WORKDIR /tmp
# SQLite
RUN wget https://www.sqlite.org/2022/sqlite-autoconf-3390200.tar.gz
RUN tar xvf ./sqlite-autoconf-3390200.tar.gz
RUN ./sqlite-autoconf-3390200/configure --prefix=/usr/local
RUN make install

# RUN wget https://www.python.org/ftp/python/3.9.13/Python-3.9.13.tgz

COPY ./docker/Python-3.9.13.tgz ./
RUN tar xvf ./Python-3.9.13.tgz
RUN ./Python-3.9.13/configure --prefix=/usr/local --enable-optimizations --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
RUN make altinstall

COPY ./requirements.txt .
RUN pip3.9 install -r ./requirements.txt
RUN pip3.9 install mod_wsgi

COPY ./docker/wsgi.conf /etc/httpd/conf.d/
RUN mv /etc/httpd/conf.d/welcome.conf /etc/httpd/conf.d/welcome.conf_bk
RUN mkdir /var/www/Asobi
COPY . /var/www/Asobi/
RUN chown -R apache:apache /var/www/Asobi/

EXPOSE 80
ENTRYPOINT ["/usr/sbin/httpd","-DFOREGROUND"]
