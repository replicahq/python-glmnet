# This is going to be a Frankenstein's monster of
# a build file based on that from https://github.com/amolenaar/meson-python-pdm-example
# and whatever I need to steal from Scipy to get this to work
project('glmnet', 'c',
  version : '2.6.0',
  meson_version: '>= 1.5.0',
  default_options : [
    'warning_level=1',
    'fortran_std=legacy',
    'buildtype=debugoptimized',
    ])

# https://mesonbuild.com/Python-module.html
# requires atleast 0.46.0
py_mod = import('python')
py3 = py_mod.find_installation()
py3_dep = py3.dependency()

cc = meson.get_compiler('c')

# Check compiler is recent enough (see "Toolchain Roadmap" for details)
_global_c_args = cc.get_supported_arguments(
  '-Wno-unused-but-set-variable',
  '-Wno-unused-function',
  '-Wno-conversion',
  '-Wno-misleading-indentation',
)
add_project_arguments(_global_c_args, language : 'c')

m_dep = cc.find_library('m', required : false)
if m_dep.found()
  add_project_link_arguments('-lm', language : 'c')
endif

# setup fortran
add_languages('fortran', native: false)
ff = meson.get_compiler('fortran')
if ff.has_argument('-Wno-conversion')
  add_project_arguments('-Wno-conversion', language: 'fortran')
endif

_global_ff_args = ff.get_supported_arguments(
  # '-fallow-argument-mismatch',
  '-fdefault-real-8',
  '-ffixed-form',
  '-fallow-argument-mismatch',
  '-fno-optimize-sibling-calls',
  '-w',
)
add_project_arguments(_global_ff_args, language: 'fortran')
add_project_arguments('-ffixed-form', language: 'fortran')

if host_machine.system() == 'darwin'
  if cc.has_link_argument('-Wl,-ld_classic')
    # New linker introduced in macOS 14 not working yet, see gh-19357 and gh-19387
    add_project_link_arguments('-Wl,-ld_classic', language : ['c', 'fortran'])
  endif
  if cc.has_link_argument('-Wl,-dead_strip')
    # Allow linker to strip unused symbols
    add_project_link_arguments('-Wl,-dead_strip', language : ['c', 'fortran'])
  endif
endif

# Hide symbols when building on Linux with GCC. For Python extension modules,
# we only need `PyInit_*` to be public, anything else may cause problems. So we
# use a linker script to avoid exporting those symbols (this is in addition to
# Meson using `-fvisibility=hidden` for C and `-fvisibility-inlines-hidden` for
# C++ code. See gh-15996 for details.
_linker_script = meson.project_source_root() / 'scipy/_build_utils/link-version-pyinit.map'
version_link_args = ['-Wl,--version-script=' + _linker_script]
# Note that FreeBSD only accepts version scripts when -shared is passed,
# hence we need to pass that to `cc.links` explicitly (flag is already
# present for `extension_module` invocations).
if not cc.links('', name: '-Wl,--version-script', args: ['-shared', version_link_args])
  version_link_args = []
endif

_linker_script = meson.project_source_root() / 'scipy/_build_utils/link-version-pyinit.map'
version_link_args = ['-Wl,--version-script=' + _linker_script]

# Fortran warning flags
_fflag_Wno_argument_mismatch = ff.get_supported_arguments('-Wno-argument-mismatch')
_fflag_Wno_conversion = ff.get_supported_arguments('-Wno-conversion')
_fflag_Wno_intrinsic_shadow = ff.get_supported_arguments('-Wno-intrinsic-shadow')
_fflag_Wno_maybe_uninitialized = ff.get_supported_arguments('-Wno-maybe-uninitialized')
_fflag_Wno_surprising = ff.get_supported_arguments('-Wno-surprising')
_fflag_Wno_uninitialized = ff.get_supported_arguments('-Wno-uninitialized')
_fflag_Wno_unused_dummy_argument = ff.get_supported_arguments('-Wno-unused-dummy-argument')
_fflag_Wno_unused_label = ff.get_supported_arguments('-Wno-unused-label')
_fflag_Wno_unused_variable = ff.get_supported_arguments('-Wno-unused-variable')
_fflag_Wno_tabs = ff.get_supported_arguments('-Wno-tabs')
# The default list of warnings to ignore from Fortran code. There is a lot of
# old, vendored code that is very bad and we want to compile it silently (at
# least with GCC and Clang)
fortran_ignore_warnings = ff.get_supported_arguments(
 _fflag_Wno_argument_mismatch,
 _fflag_Wno_conversion,
 _fflag_Wno_maybe_uninitialized,
 _fflag_Wno_unused_dummy_argument,
 _fflag_Wno_unused_label,
 _fflag_Wno_unused_variable,
 _fflag_Wno_tabs,
)


incdir_numpy = meson.get_external_property('numpy-include-dir', 'not-given')
if incdir_numpy == 'not-given'
  incdir_numpy = run_command(py3,
    [
      '-c',
      '''import os
import numpy as np
try:
  incdir = os.path.relpath(np.get_include())
except Exception:
  incdir = np.get_include()
print(incdir)
  '''
    ],
    check: true
  ).stdout().strip()

  # We do need an absolute path to feed to `cc.find_library` below
  _incdir_numpy_abs = run_command(py3,
    [
      '-c',
      '''import os
os.chdir("..")
import numpy
print(numpy.get_include())
      '''
    ],
    check: true
  ).stdout().strip()
else
  _incdir_numpy_abs = incdir_numpy
endif

inc_np = include_directories(incdir_numpy)
incdir_f2py = run_command(py3,
  [
  '-c',
  'import os; from numpy import f2py; incdir = os.path.relpath(f2py.get_include()); print(incdir)',
  ],
  check: true
).stdout().strip()

inc_f2py = include_directories(incdir_f2py)
fortranobject_c = incdir_f2py / 'fortranobject.c'


numpy_nodepr_api = ['-DNPY_NO_DEPRECATED_API=NPY_1_9_API_VERSION']
np_dep = declare_dependency(include_directories: inc_np, compile_args: numpy_nodepr_api)

fortranobject_lib = static_library('_fortranobject',
  fortranobject_c,
  c_args: numpy_nodepr_api,
  dependencies: py3_dep,
  include_directories: [inc_np, inc_f2py],
  gnu_symbol_visibility: 'hidden',
)
fortranobject_dep = declare_dependency(
  link_with: fortranobject_lib,
  include_directories: [inc_np, inc_f2py],
)

# setup f2py in the style of Scipy
generate_f2pymod = find_program('tools/generate_f2pymod.py')
f2py = find_program('f2py')

f2py_gen = generator(generate_f2pymod,
  arguments : ['@INPUT@', '-o', '@BUILD_DIR@'],
  output : ['_@BASENAME@module.c', '_@BASENAME@-f2pywrappers.f'],
)

subdir('src/glmnet')
