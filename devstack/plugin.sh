# plugin.sh - DevStack plugin.sh dispatch script barbican-ui

BARBICAN_UI_DIR=$(cd $(dirname $BASH_SOURCE)/.. && pwd)

function install_barbican_ui {
    # NOTE(shu-mutou): workaround for devstack bug: 1540328
    # where devstack install 'test-requirements' but should not do it
    # for barbican-ui project as it installs Horizon from url.
    # Remove following two 'mv' commands when mentioned bug is fixed.
    mv $BARBICAN_UI_DIR/test-requirements.txt $BARBICAN_UI_DIR/_test-requirements.txt

    setup_develop ${BARBICAN_UI_DIR}

    mv $BARBICAN_UI_DIR/_test-requirements.txt $BARBICAN_UI_DIR/test-requirements.txt
}

function configure_barbican_ui {
    cp -a ${BARBICAN_UI_DIR}/barbican_ui/enabled/* ${DEST}/horizon/openstack_dashboard/local/enabled/
}

# check for service enabled
if is_service_enabled barbican-ui; then

    if [[ "$1" == "stack" && "$2" == "pre-install"  ]]; then
        # Set up system services
        # no-op
        :

    elif [[ "$1" == "stack" && "$2" == "install"  ]]; then
        # Perform installation of service source
        echo_summary "Installing Barbican UI"
        install_barbican_ui

    elif [[ "$1" == "stack" && "$2" == "post-config"  ]]; then
        # Configure after the other layer 1 and 2 services have been configured
        echo_summary "Configuring Barbican UI"
        configure_barbican_ui

    elif [[ "$1" == "stack" && "$2" == "extra"  ]]; then
        # no-op
        :
    fi

    if [[ "$1" == "unstack"  ]]; then
        # no-op
        :
    fi

    if [[ "$1" == "clean"  ]]; then
        # Remove state and transient data
        # Remember clean.sh first calls unstack.sh
        # no-op
        :
    fi
fi