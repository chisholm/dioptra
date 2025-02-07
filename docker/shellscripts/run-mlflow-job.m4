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

# m4_ignore(
echo "This is just a script template, not the script (yet) - pass it to 'argbash' to fix this." >&2
exit 11 #)Created by argbash-init v2.8.1
# ARG_OPTIONAL_SINGLE([backend],[],[[dioptra|local] Execution backend for MLFlow],[dioptra])
# ARG_OPTIONAL_SINGLE([conda-env],[],[Conda environment (deprecated, to be removed in future release)],[base])
# ARG_OPTIONAL_SINGLE([experiment-id],[],[ID of the experiment under which to launch the run],[])
# ARG_OPTIONAL_SINGLE([entry-point],[],[MLproject entry point to invoke],[main])
# ARG_OPTIONAL_SINGLE([mlflow-run-module],[],[Python module used to invoke 'mlflow run'],[dioptra.rq.cli.mlflow])
# ARG_OPTIONAL_SINGLE([s3-workflow],[],[S3 URI to a tarball or zip archive containing scripts and a MLproject file defining a workflow],[])
# ARG_USE_ENV([DIOPTRA_PLUGIN_DIR],[],[Directory in worker container for syncing the builtin plugins])
# ARG_USE_ENV([DIOPTRA_PLUGINS_S3_URI],[],[S3 URI to the directory containing the builtin plugins])
# ARG_USE_ENV([DIOPTRA_CUSTOM_PLUGINS_S3_URI],[],[S3 URI to the directory containing the custom plugins])
# ARG_USE_ENV([MLFLOW_S3_ENDPOINT_URL],[],[The S3 endpoint URL])
# ARG_LEFTOVERS([Entry point keyword arguments (optional)])
# ARG_DEFAULTS_POS
# ARGBASH_SET_INDENT([  ])
# ARG_HELP([Execute a job defined in a MLproject file.\n])"
# ARGBASH_GO

# [ <-- needed because of Argbash
shopt -s extglob
set -euo pipefail

###########################################################################################
# Global parameters
###########################################################################################

readonly dioptra_plugin_dir="${DIOPTRA_PLUGIN_DIR-}"
readonly dioptra_plugins_s3_uri="${DIOPTRA_PLUGINS_S3_URI-}"
readonly dioptra_custom_plugins_s3_uri="${DIOPTRA_CUSTOM_PLUGINS_S3_URI-}"
readonly entry_point_kwargs="${_arg_leftovers[*]}"
readonly entry_point="${_arg_entry_point}"
readonly logname="Run MLFlow Job"
readonly mlflow_backend="${_arg_backend}"
readonly mlflow_experiment_id="${_arg_experiment_id}"
readonly mlflow_run_module="${_arg_mlflow_run_module}"
readonly mlflow_s3_endpoint_url="${MLFLOW_S3_ENDPOINT_URL-}"
readonly s3_workflow_uri="${_arg_s3_workflow}"

readonly workflow_filename="$(basename ${s3_workflow_uri} 2>/dev/null)"

###########################################################################################
# Validate MLFlow-related option flags
#
# Globals:
#   logname
#   mlflow_backend
#   mlflow_experiment_id
#   mlflow_s3_endpoint_url
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

validate_mlflow_inputs() {
  if [[ -z ${mlflow_experiment_id} ]]; then
    echo "${logname}: ERROR - --experiment-id option not set" 1>&2
    exit 1
  fi

  if [[ -z ${mlflow_s3_endpoint_url} ]]; then
    echo "${logname}: ERROR - MLFLOW_S3_ENDPOINT_URL environment variable not set" 1>&2
    exit 1
  fi

  case ${mlflow_backend} in
    dioptra | local) ;;
    *)
      echo "${logname}: ERROR - --backend option must be \"dioptra\" or \"local\"" 1>&2
      exit 1
      ;;
  esac
}

###########################################################################################
# Unpack workflow archive
#
# Globals:
#   workflow_filename
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

unpack_workflow_archive() {
  local filepath="$(pwd)/${workflow_filename}"

  if [[ -f ${filepath} && -f /usr/local/bin/unpack-archive.sh ]]; then
    /usr/local/bin/unpack-archive.sh ${filepath}
  elif [[ ! -f /usr/local/bin/unpack-archive.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/unpack-archive.sh script missing" 1>&2
    exit 1
  elif [[ ! -f ${filepath} ]]; then
    echo "${logname}: ERROR - workflow archive file missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Download workflow from S3 storage
#
# Globals:
#   mlflow_s3_endpoint_url
#   s3_workflow_uri
#   workflow_filename
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

download_workflow() {
  local src="${s3_workflow_uri}"
  local dest="$(pwd)/${workflow_filename}"

  if [[ ! -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-cp.sh ]]; then
    /usr/local/bin/s3-cp.sh --endpoint-url ${mlflow_s3_endpoint_url} ${src} ${dest}
  elif [[ -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-cp.sh ]]; then
    /usr/local/bin/s3-cp.sh ${src} ${dest}
  elif [[ ! -f /usr/local/bin/s3-cp.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/s3-cp.sh script missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Clear plugins directories
#
# Globals:
#   dioptra_plugin_dir
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

clear_plugins_dirs() {
  local plugin_dirs=(
    "${dioptra_plugin_dir}/dioptra_builtins"
    "${dioptra_plugin_dir}/dioptra_custom"
  )

  for dir in "${plugin_dirs[@]}"; do
    if [[ -d "${dir}" ]]; then
      if ! rm -rf "${dir}"; then
        echo "${logname}: ERROR - Unexpected error while clearing the plugin directories." 1>&2
        exit 1
      fi
    fi
  done
}

###########################################################################################
# Synchronize builtin plugins from S3 storage
#
# Globals:
#   dioptra_plugin_dir
#   dioptra_plugins_s3_uri
#   mlflow_s3_endpoint_url
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

sync_builtin_plugins() {
  local src="${dioptra_plugins_s3_uri}"
  local dest="${dioptra_plugin_dir}/dioptra_builtins"

  if [[ ! -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-sync.sh ]]; then
    /usr/local/bin/s3-sync.sh --endpoint-url ${mlflow_s3_endpoint_url} --delete ${src} ${dest}
  elif [[ -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-sync.sh ]]; then
    /usr/local/bin/s3-sync.sh --delete ${src} ${dest}
  elif [[ ! -f /usr/local/bin/s3-sync.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/s3-sync.sh script missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Synchronize custom plugins from S3 storage
#
# Globals:
#   dioptra_plugin_dir
#   dioptra_custom_plugins_s3_uri
#   mlflow_s3_endpoint_url
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

sync_custom_plugins() {
  local src="${dioptra_custom_plugins_s3_uri}"
  local dest="${dioptra_plugin_dir}/dioptra_custom"

  if [[ ! -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-sync.sh ]]; then
    /usr/local/bin/s3-sync.sh --endpoint-url ${mlflow_s3_endpoint_url} --delete ${src} ${dest}
  elif [[ -z ${mlflow_s3_endpoint_url} && -f /usr/local/bin/s3-sync.sh ]]; then
    /usr/local/bin/s3-sync.sh --delete ${src} ${dest}
  elif [[ ! -f /usr/local/bin/s3-sync.sh ]]; then
    echo "${logname}: ERROR - /usr/local/bin/s3-sync.sh script missing" 1>&2
    exit 1
  fi
}

###########################################################################################
# Start MLFlow pipeline defined in MLproject file
#
# Globals:
#   entry_point
#   entry_point_kwargs
#   mlflow_backend
#   mlflow_experiment_id
#   mlflow_run_module
# Arguments:
#   None
# Returns:
#   None
###########################################################################################

start_mlflow() {
  local workflow_filepath="$(pwd)/${workflow_filename}"
  local mlflow_backend_opts="--backend ${mlflow_backend}\
  --backend-config {\"workflow_filepath\":\"${workflow_filepath}\"}"
  local mlproject_file=$(find . -name MLproject -type f -print)

  if [[ -z ${mlproject_file} ]]; then
    echo "${logname}: ERROR - missing MLproject file" 1>&2
    exit 1
  fi

  local mlproject_dir=$(dirname ${mlproject_file})

  echo "${logname}: mlproject file found - ${mlproject_file}"
  echo "${logname}: starting mlflow pipeline"
  echo "${logname}: mlflow run options - --no-conda ${mlflow_backend_opts}\
  --experiment-id ${mlflow_experiment_id} -e ${entry_point} ${entry_point_kwargs}"

  python -m ${mlflow_run_module} run --no-conda \
    ${mlflow_backend_opts} \
    --experiment-id ${mlflow_experiment_id} \
    -e ${entry_point} \
    ${entry_point_kwargs} \
    ${mlproject_dir}
}

###########################################################################################
# Main script
###########################################################################################

validate_mlflow_inputs
clear_plugins_dirs
sync_builtin_plugins
sync_custom_plugins
download_workflow
unpack_workflow_archive
start_mlflow
# ] <-- needed because of Argbash
