%global with_debug 1

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%if ! 0%{?gobuild:1}
%define gobuild(o:) go build -buildmode pie -tags=rpm_crashtraceback -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '-Wl,-z,relro,-z,now'" -a -v -x %{?**};
%endif

%global provider        github
%global provider_tld    com
%global project         coreos
%global repo            etcd
# https://github.com/coreos/etcd
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          3ac81f3ae2264b21871128a170c78f8a9b2a3187
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

%global system_name     etcd
%global man_version     3.2.21

Name:		etcd
Version:	3.2.21
Release:	2%{?dist}
Summary:	A highly-available key value store for shared configuration
License:	ASL 2.0
URL:		https://%{provider_prefix}
Source0:	https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz
Source1:	%{system_name}.service
Source2:	%{system_name}.conf
Source3:        man-%{man_version}.tar.gz
Patch3:         bz1350875-disaster-recovery-with-copies.patch
Patch4:         expand-etcd-arch-validation.patch

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:x86_64 aarch64 ppc64le s390x}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
#BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}
BuildRequires:  compiler(go-compiler)

Obsoletes: etcd3 < 3.0.15
Provides: etcd3 = %{version}-%{release}

BuildRequires: libpcap-devel

BuildRequires:	systemd

Requires(pre):	shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
A highly-available key value store for shared configuration.

%{?enable_gotoolset7}

%prep
%setup -q -n man-%{man_version} -T -b 3
%setup -q -n %{repo}-%{commit}
mkdir -p man/man1
cp ../man-%{man_version}/*.1 man/man1/.

# move content of vendor under Godeps as has been so far
mkdir -p Godeps/_workspace/src
mv cmd/vendor/* Godeps/_workspace/src/.

%patch3 -p1
%patch4 -p1

%build
mkdir -p src/github.com/coreos
ln -s ../../../ src/github.com/coreos/etcd

export GOPATH=$(pwd):$(pwd)/Godeps/_workspace:%{gopath}

export LDFLAGS="-X %{import_path}/version.GitSHA=%{shortcommit} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \n')"

%gobuild -o bin/%{system_name} %{import_path}
%gobuild -o bin/%{system_name}ctl %{import_path}/%{system_name}ctl

%install
install -D -p -m 0755 bin/%{system_name} %{buildroot}%{_bindir}/%{system_name}
install -D -p -m 0755 bin/%{system_name}ctl %{buildroot}%{_bindir}/%{system_name}ctl
install -D -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{system_name}.service
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{system_name}
install -m 644 -t %{buildroot}%{_sysconfdir}/%{system_name} %{SOURCE2}

# install manpages
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 man/man1/* %{buildroot}%{_mandir}/man1

# And create /var/lib/etcd
install -d -m 0755 %{buildroot}%{_sharedstatedir}/%{system_name}

%pre
getent group %{system_name} >/dev/null || groupadd -r %{system_name}
getent passwd %{system_name} >/dev/null || useradd -r -g %{system_name} -d %{_sharedstatedir}/%{system_name} \
	-s /sbin/nologin -c "etcd user" %{system_name}

%post
%systemd_post %{system_name}.service

%preun
%systemd_preun %{system_name}.service

%postun
%systemd_postun %{system_name}.service

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE
%doc *.md
%doc glide.lock
%config(noreplace) %{_sysconfdir}/%{system_name}
%{_bindir}/%{system_name}
%{_bindir}/%{system_name}ctl
%dir %attr(-,%{system_name},%{system_name}) %{_sharedstatedir}/%{system_name}
%{_unitdir}/%{system_name}.service
%{_mandir}/man1/*.1*

%changelog
* Tue Aug 11 2020 jiangxinyu <jiangxinyu@kylinos.cn> - 3.2.21-2
- Init etcd project
