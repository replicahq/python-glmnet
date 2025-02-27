py3.extension_module('_glmnet',
  [
    f2py_gen.process('glmnet.pyf'),
    'src/glmnet5.f90',
  ],
  include_directories: inc_np,
  fortran_args: [fortran_ignore_warnings, _fflag_Wno_surprising],
  dependencies: [py3_dep, fortranobject_dep],
  link_with: fortranobject_lib,
  link_language: 'fortran',
  install : true,
  subdir: 'glmnet'
)

py3.install_sources(
  [
    '__init__.py',
    'doc.py',
    'errors.py',
    'linear.py',
    'logistic.py',
    'scorer.py',
    'util.py',
  ],
  pure : false,
  subdir : 'glmnet'
)


# subdir('_glmnet')