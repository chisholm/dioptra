#!/bin/bash
# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode

# Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([restapi-host],[],[Dioptra REST API Service host],[restapi])
# ARG_OPTIONAL_SINGLE([restapi-port],[],[Dioptra REST API Service port],[5000])
# ARG_OPTIONAL_SINGLE([mlflow-tracking-host],[],[MLflow Tracking Service host],[mlflow-tracking])
# ARG_OPTIONAL_SINGLE([mlflow-tracking-port],[],[MLflow Tracking Service port],[5000])
# ARG_OPTIONAL_SINGLE([nginx-restapi-port],[],[Nginx Dioptra REST API listening port],[30080])
# ARG_OPTIONAL_SINGLE([nginx-mlflow-port],[],[Nginx MLflow Tracking listening port],[35000])
# ARG_DEFAULTS_POS()
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Nginx Entry Point\n])"
# ARGBASH_GO()
# needed because of Argbash --> m4_ignore([
### START OF CODE GENERATED BY Argbash v2.10.0 one line above ###
# Argbash is a bash code generator used to get arguments parsing right.
# Argbash is FREE SOFTWARE, see https://argbash.io for more info


die()
{
  local _ret="${2:-1}"
  test "${_PRINT_HELP:-no}" = yes && print_help >&2
  echo "$1" >&2
  exit "${_ret}"
}


begins_with_short_option()
{
  local first_option all_short_options='h'
  first_option="${1:0:1}"
  test "$all_short_options" = "${all_short_options/$first_option/}" && return 1 || return 0
}

# THE DEFAULTS INITIALIZATION - OPTIONALS
_arg_restapi_host="restapi"
_arg_restapi_port="5000"
_arg_mlflow_tracking_host="mlflow-tracking"
_arg_mlflow_tracking_port="5000"
_arg_nginx_restapi_port="30080"
_arg_nginx_mlflow_port="35000"


print_help()
{
  printf '%s\n' "Nginx Entry Point
"
  printf 'Usage: %s [--restapi-host <arg>] [--restapi-port <arg>] [--mlflow-tracking-host <arg>] [--mlflow-tracking-port <arg>] [--nginx-restapi-port <arg>] [--nginx-mlflow-port <arg>] [-h|--help]\n' "$0"
  printf '\t%s\n' "--restapi-host: Dioptra REST API Service host (default: 'restapi')"
  printf '\t%s\n' "--restapi-port: Dioptra REST API Service port (default: '5000')"
  printf '\t%s\n' "--mlflow-tracking-host: MLflow Tracking Service host (default: 'mlflow-tracking')"
  printf '\t%s\n' "--mlflow-tracking-port: MLflow Tracking Service port (default: '5000')"
  printf '\t%s\n' "--nginx-restapi-port: Nginx Dioptra REST API listening port (default: '30080')"
  printf '\t%s\n' "--nginx-mlflow-port: Nginx MLflow Tracking listening port (default: '35000')"
  printf '\t%s\n' "-h, --help: Prints help"
}


parse_commandline()
{
  while test $# -gt 0
  do
    _key="$1"
    case "$_key" in
      --restapi-host)
        test $# -lt 2 && die "Missing value for the optional argument '$_key'." 1
        _arg_restapi_host="$2"
        shift
        ;;
      --restapi-host=*)
        _arg_restapi_host="${_key##--restapi-host=}"
        ;;
      --restapi-port)
        test $# -lt 2 && die "Missing value for the optional argument '$_key'." 1
        _arg_restapi_port="$2"
        shift
        ;;
      --restapi-port=*)
        _arg_restapi_port="${_key##--restapi-port=}"
        ;;
      --mlflow-tracking-host)
        test $# -lt 2 && die "Missing value for the optional argument '$_key'." 1
        _arg_mlflow_tracking_host="$2"
        shift
        ;;
      --mlflow-tracking-host=*)
        _arg_mlflow_tracking_host="${_key##--mlflow-tracking-host=}"
        ;;
      --mlflow-tracking-port)
        test $# -lt 2 && die "Missing value for the optional argument '$_key'." 1
        _arg_mlflow_tracking_port="$2"
        shift
        ;;
      --mlflow-tracking-port=*)
        _arg_mlflow_tracking_port="${_key##--mlflow-tracking-port=}"
        ;;
      --nginx-restapi-port)
        test $# -lt 2 && die "Missing value for the optional argument '$_key'." 1
        _arg_nginx_restapi_port="$2"
        shift
        ;;
      --nginx-restapi-port=*)
        _arg_nginx_restapi_port="${_key##--nginx-restapi-port=}"
        ;;
      --nginx-mlflow-port)
        test $# -lt 2 && die "Missing value for the optional argument '$_key'." 1
        _arg_nginx_mlflow_port="$2"
        shift
        ;;
      --nginx-mlflow-port=*)
        _arg_nginx_mlflow_port="${_key##--nginx-mlflow-port=}"
        ;;
      -h|--help)
        print_help
        exit 0
        ;;
      -h*)
        print_help
        exit 0
        ;;
      *)
        _PRINT_HELP=yes die "FATAL ERROR: Got an unexpected argument '$1'" 1
        ;;
    esac
    shift
  done
}

parse_commandline "$@"

# OTHER STUFF GENERATED BY Argbash

### END OF CODE GENERATED BY Argbash (sortof) ### ])
# [ <-- needed because of Argbash

shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly restapi_host="${_arg_restapi_host}"
readonly restapi_port="${_arg_restapi_port}"
readonly mlflow_tracking_host="${_arg_mlflow_tracking_host}"
readonly mlflow_tracking_port="${_arg_mlflow_tracking_port}"
readonly nginx_restapi_port="${_arg_nginx_restapi_port}"
readonly nginx_mlflow_port="${_arg_nginx_mlflow_port}"
readonly logname="Container Entry Point"

###########################################################################################
# Secure the container at runtime
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

secure_container() {
  if [[ -f /usr/local/bin/secure-container.sh ]]; then
    /usr/local/bin/secure-container.sh
  else
    echo "${logname}: ERROR - /usr/local/bin/secure-container.sh script missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Set nginx configuration variables
#
# Globals:
#   mlflow_tracking_host
#   mlflow_tracking_port
#   nginx_restapi_port
#   nginx_mlflow_port
#   restapi_host
#   restapi_port
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

set_nginx_variables() {
  echo "${logname}: INFO - Set nginx variables  |  \
  MLFLOW_TRACKING_HOST=${mlflow_tracking_host} \
  MLFLOW_TRACKING_PORT=${mlflow_tracking_port} \
  NGINX_MLFLOW_PORT=${nginx_mlflow_port} \
  NGINX_RESTAPI_PORT=${nginx_restapi_port} \
  RESTAPI_HOST=${restapi_host} \
  RESTAPI_PORT=${restapi_port}"
  sed -i -e 's/$MLFLOW_TRACKING_HOST/'"${mlflow_tracking_host}"'/g' \
    /etc/nginx/conf.d/default.conf
  sed -i -e 's/$MLFLOW_TRACKING_PORT/'"${mlflow_tracking_port}"'/g' \
    /etc/nginx/conf.d/default.conf
  sed -i -e 's/$NGINX_MLFLOW_PORT/'"${nginx_mlflow_port}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$NGINX_RESTAPI_PORT/'"${nginx_restapi_port}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$RESTAPI_HOST/'"${restapi_host}"'/g' /etc/nginx/conf.d/default.conf
  sed -i -e 's/$RESTAPI_PORT/'"${restapi_port}"'/g' /etc/nginx/conf.d/default.conf

  local default_conf=$(cat /etc/nginx/conf.d/default.conf)
  echo "${logname}: INFO - Updated contents of /etc/nginx/conf.d/default.conf"
  echo "${default_conf}"
}

###########################################################################################
# Start nginx server
#
# Globals:
#   None
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_nginx() {
  echo "${logname}: INFO - Starting Nginx process"
  /usr/sbin/nginx
}

###########################################################################################
# Main script
###########################################################################################

secure_container
set_nginx_variables
start_nginx
# ] <-- needed because of Argbash
