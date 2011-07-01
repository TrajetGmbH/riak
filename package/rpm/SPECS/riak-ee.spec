# _revision, _release, and _version should be defined on the rpmbuild command
# line like so:
#
# --define "_version 0.9.1.19.abcdef" --define "_release 7" \
# --define "_revision 0.9.1-19-abcdef"

%define appname                riak
%define appuser                riak

Name: riak-ee
Version: %{_version}
Release: %{_release}%{?dist}
License: Proprietary
Group: Development/Libraries
Source: %{name}-%{_revision}.tar.gz
Source1: riak_init
URL: http://basho.com
Vendor: Basho Technologies
Packager: Basho Technologies <riak-user@lists.basho.com>
BuildRoot: %{_tmppath}/%{name}-%{_revision}-%{release}-root
Summary: Riak Distributed Data Store
Obsoletes: riak

%description
Riak is a distrubuted data store.

%define riak_lib %{_libdir}/%{appname}
%define init_script %{_sysconfdir}/init.d/%{appname}

%define __prelink_undo_cmd /bin/cat prelink library
%define debug_package %{nil}

%define platform_bin_dir %{_sbindir}
%define platform_data_dir %{_localstatedir}/lib/%{appname}
%define platform_etc_dir %{_sysconfdir}/%{appname}
%define platform_lib_dir %{riak_lib}
%define platform_log_dir %{_localstatedir}/log/%{appname}

%prep
%setup -q -n %{_repo}-%{_revision}
cat > rel/vars.config <<EOF
% app.config
{web_ip,            "127.0.0.1"}.
{web_port,          8098}.
{handoff_port,      8099}.
{pb_ip,             "127.0.0.1"}.
{pb_port,           8087}.
{ring_state_dir,        "%{platform_data_dir}/ring"}.
{bitcask_data_root,     "%{platform_data_dir}/bitcask"}.
{leveldb_data_root,     "%{platform_data_dir}/leveldb"}.
{merge_index_data_root, "%{platform_data_dir}/merge_index"}.
{merge_index_data_root_2i, "%{platform_data_dir}/merge_index_2i"}.
{sasl_error_log,        "%{platform_log_dir}/sasl-error.log"}.
{sasl_log_dir,          "%{platform_log_dir}/sasl"}.
{mapred_queue_dir,      "%{platform_data_dir}/mr_queue"}.
{repl_data_root,        "%{platform_data_dir}/riak_repl"}.
{snmp_agent_conf,       "%{platform_etc_dir}/snmp/agent/conf"}.
{snmp_db_dir,           "%{platform_data_dir}/snmp/agent/db"}.
{map_js_vms,   8}.
{reduce_js_vms, 6}.
{hook_js_vms, 2}.
% Platform-specific installation paths
{platform_bin_dir,  "%{platform_bin_dir}"}.
{platform_data_dir, "%{platform_data_dir}"}.
{platform_etc_dir,  "%{platform_etc_dir}"}.
{platform_lib_dir,  "%{platform_lib_dir}"}.
{platform_log_dir,  "%{platform_log_dir}"}.
% vm.args
{node,              "riak@127.0.0.1"}.
{crash_dump,        "%{platform_log_dir}/erl_crash.dump"}.
% bin/riak*
{runner_script_dir, "%{platform_bin_dir}"}.
{runner_base_dir,   "%{platform_lib_dir}"}.
{runner_etc_dir,    "%{platform_etc_dir}"}.
{runner_log_dir,    "%{platform_log_dir}"}.
{pipe_dir,          "%{_localstatedir}/run/%{appname}/"}.
{runner_user,       "%{appuser}"}.
% etc/snmp/agent.conf
{snmp_agent_port,    4000}.
EOF


%build
#mkdir %{appname}
#
# Temporary work around for Blaire
#
#make rel
make deps compile
RIAK_SNMP=apps/riak_snmp
if [ -d deps/riak_snmp ]; then
    RIAK_SNMP=deps/riak_snmp
fi
export RIAK_SNMP
cp ${RIAK_SNMP}/mibs/* ${RIAK_SNMP}/priv/mibs/
make rel

%install
%define releasepath	%{_builddir}/%{buildsubdir}/rel/%{appname}

mkdir -p %{buildroot}%{platform_etc_dir}
mkdir -p %{buildroot}%{platform_lib_dir}
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{platform_data_dir}/dets
mkdir -p %{buildroot}%{platform_data_dir}/bitcask
mkdir -p %{buildroot}%{platform_data_dir}/ring
mkdir -p %{buildroot}%{platform_data_dir}/riak_repl
mkdir -p %{buildroot}%{platform_data_dir}/snmp/agent/db
mkdir -p %{buildroot}%{platform_log_dir}/sasl
mkdir -p %{buildroot}%{platform_log_dir}/riak_repl
mkdir -p %{buildroot}%{platform_data_dir}/mr_queue
mkdir -p %{buildroot}%{_localstatedir}/run/%{appname}

#Copy all necessary lib files etc.
cp -r %{releasepath}/lib %{buildroot}%{platform_lib_dir}
cp -r %{releasepath}/erts-* %{buildroot}%{platform_lib_dir}
cp -r %{releasepath}/releases %{buildroot}%{platform_lib_dir}
cp -r $RPM_BUILD_DIR/%{_repo}-%{_revision}/doc/man/man1/*.gz \
		%{buildroot}%{_mandir}/man1
# snmp data
cp -r %{releasepath}/etc/snmp %{buildroot}/%{platform_etc_dir}/
cp -r %{releasepath}/data/snmp \
		%{buildroot}/%{platform_data_dir}/
# inter-data center replication
install -p -D -m 0644 \
		%{releasepath}/etc/app.config \
		%{buildroot}%{platform_etc_dir}/
install -p -D -m 0644 \
		%{releasepath}/etc/vm.args \
		%{buildroot}%{platform_etc_dir}/
install -p -D -m 0755 \
		%{releasepath}/bin/%{appname} \
		%{buildroot}/%{platform_bin_dir}/%{appname}
install -p -D -m 0755 \
		%{releasepath}/bin/%{appname}-admin \
		%{buildroot}/%{platform_bin_dir}/%{appname}-admin
install -p -D -m 0755 \
		%{releasepath}/bin/%{appname}-repl \
		%{buildroot}/%{platform_bin_dir}/%{appname}-repl
install -p -D -m 0755 \
		%{releasepath}/bin/search-cmd \
		%{buildroot}/%{platform_bin_dir}/search-cmd
install -p -D -m 0755 %{SOURCE1} %{buildroot}/%{init_script}

# Needed to work around check-rpaths which seems to be hardcoded into recent
# RPM releases
export QA_RPATHS=3


%pre
# create riak group only if it doesn't already exist
if ! getent group %{appuser} >/dev/null 2>&1; then
        groupadd -r %{appuser}
fi

# create riak user only if it doesn't already exist
if getent passwd %{appuser} >/dev/null 2>&1; then
	# make sure it has the right home dir if the user already exists
	usermod -d %{platform_data_dir} %{appuser}
else
        useradd -r -g %{appuser} --home %{platform_data_dir} \
			%{appuser}
        usermod -c "Riak Server" %{appuser}
fi

%post
# Fixup perms for SELinux
find %{platform_lib_dir} -name "*.so" -exec chcon -t textrel_shlib_t {} \;

%files
%defattr(-,riak,riak)
%{_libdir}/*
%dir %{platform_etc_dir}
%config(noreplace) %{platform_etc_dir}/*
%attr(0755,root,root) %{init_script}
%attr(0755,root,root) %{platform_bin_dir}/%{appname}
%attr(0755,root,root) %{platform_bin_dir}/%{appname}-admin
%attr(0755,root,root) %{platform_bin_dir}/%{appname}-repl
%attr(0755,root,root) %{platform_bin_dir}/search-cmd
%attr(0644,root,root) %{_mandir}/man1/*
%{platform_data_dir}
%{platform_log_dir}
%{_localstatedir}/run/%{appname}

%clean
rm -rf %{buildroot}