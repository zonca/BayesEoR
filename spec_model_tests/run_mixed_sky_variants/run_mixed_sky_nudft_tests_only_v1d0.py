#!/users/psims/anaconda2/bin/python

#--------------------------------------------
# Imports
#--------------------------------------------
from subprocess import os
import sys
# head,tail = os.path.split(os.getcwd())
head,tail = os.path.split(os.path.split(os.getcwd())[0])
sys.path.append(head)
from BayesEoR import * #Make everything available for now, this can be refined later
import BayesEoR.Params.params as p

mpi_rank = 0
# run_full_analysis = True #False skips mpi and other imports that can cause crashes in ipython (note: in ipython apparently __name__ == '__main__' whis is why this if statement is here instead)
run_full_analysis = False #When running an analysis this should be True.
# if __name__ == '__main__':
if run_full_analysis:
	import mpi4py
	from mpi4py import MPI
	mpi_comm = MPI.COMM_WORLD
	mpi_rank = mpi_comm.Get_rank()
	mpi_size = mpi_comm.Get_size()
	print 'mpi_comm', mpi_comm
	print 'mpi_rank', mpi_rank
	print 'mpi_size', mpi_size
	use_MultiNest = True #Set to false for large parameter spaces
	if use_MultiNest:
		from pymultinest.solve import solve
	else:
		import PyPolyChord.PyPolyChord as PolyChord

#--------------------------------------------
# Set analysis parameters
#--------------------------------------------
# Model Params
args = p.BayesEoRParser()
print args
npl = p.npl
print 'p.beta', p.beta
if args.beta:
	if type(args.beta)==str:
		if args.beta.count('[') and args.beta.count(']'):
			p.beta = map(float, args.beta.replace('[','').replace(']','').split(',')) #Overwrite parameter file beta with value chosen from the command line if it is included
			npl = len(p.beta) #Overwrites quadratic term when nq=2, otherwise unused.
		else:
			p.beta = float(args.beta) #Overwrite parameter file beta with value chosen from the command line if it is included 
			npl = 1
	elif type(args.beta)==list:
		p.beta = args.beta #Overwrite parameter file beta with value chosen from the command line if it is included 
		npl = len(p.beta)
	else:
		print 'No value for betas given, using defaults.'

print 'args.beta', args.beta
print 'p.beta', p.beta
print 'args.nq', args.nq

# raw_input()

nq = int(args.nq)
if nq>npl:
	nq=npl
# nq = 2 #Overwrite PCLA selection
#npl = 0 #Overwrites quadratic term when nq=2, otherwise unused.

# nq=npl=p.nq=p.npl = 0

print 'nq', nq
print 'npl', npl
sub_ML_monopole_term_model = False #Improve numerical precision. Can be used for improving numerical precision when performing evidence comparison.
sub_ML_monopole_plus_first_LW_term_model = False #Improve numerical precision. Can be used for improving numerical precision when performing evidence comparison.
sub_MLLWM = True #Improve numerical precision. DO NOT USE WHEN PERFORMING EVIDENCE COMPARISON! Can only be used for parameter estimation not evidence comparison since subtracting different MLLWM (with different evidences) from the data when comparing different LWMs will alter the relative evidences of the subtracted models. In effect subtracting a higher evidence MLLWM1 reduces the evidence for the fit to the residuals with MLLWM1 relative to fitting low evidence MLLWM2 and refitting with MLLWM2. It is only correct to compare evidences when doing no qsub or when the qsub model is fixed such as with sub_ML_monopole_term_model.
# Cube size
nf=p.nf
neta=p.neta
if not p.include_instrumental_effects:
	neta=neta -nq
nu=p.nu
nv=p.nv
nx=p.nx
ny=p.ny
# Data noise
# sigma=100.e-1
sigma=50.e-1


if p.include_instrumental_effects:
		average_baseline_redundancy = p.baseline_redundancy_array.mean() #Keep average noise level consisitent with the non-instrumental case by normalizing sigma my the average baseline redundancy before scaling individual baselines by their respective redundancies
		# sigma = sigma*average_baseline_redundancy**0.5 *1.0
		# sigma = sigma*average_baseline_redundancy**0.5 *5.0
		# sigma = sigma*average_baseline_redundancy**0.5 *20.0
		# sigma = sigma*average_baseline_redundancy**0.5 *40.0
		# sigma = sigma*average_baseline_redundancy**0.5 *100.0
		# sigma = sigma*average_baseline_redundancy**0.5 *200.0
		# sigma = sigma*average_baseline_redundancy**0.5 *250.0

		# sigma = sigma*average_baseline_redundancy**0.5 *700.0

		sigma = sigma*average_baseline_redundancy**0.5 *500.0
		# sigma = sigma*average_baseline_redundancy**0.5 *1000.0
		# sigma = sigma*average_baseline_redundancy**0.5 *2000.0
		# sigma = sigma*average_baseline_redundancy**0.5 *4000.0
		# sigma = sigma*average_baseline_redundancy**0.5 *8000.0
		# sigma = sigma*average_baseline_redundancy**0.5 *20000.0
		# sigma = sigma*average_baseline_redundancy**0.5 / 20.0
else:
	sigma = sigma*1.
	# sigma = sigma*8.


# Auxiliary and derived params
small_cube = nu<=7 and nv<=7
nuv = (nu*nv-1)
Show=False
chan_selection=''
Fz_normalisation = nf**0.5
DFT2D_Fz_normalisation = (nu*nv*nf)**0.5
n_Fourier = (nu*nv-1)*nf
n_LW = (nu*nv-1)*nq
n_model = n_Fourier+n_LW
n_dat = n_Fourier
current_file_version = 'Likelihood_v1d76_3D_ZM'
# array_save_directory = 'array_storage/{}_nu_{}_nv_{}_neta_{}_nq_{}_npl_{}_sigma_{:.1E}/'.format(current_file_version,nu,nv,neta,nq,npl,sigma).replace('.','d')
array_save_directory = 'array_storage/batch_1/{}_nu_{}_nv_{}_neta_{}_nq_{}_npl_{}_sigma_{:.1E}/'.format(current_file_version,nu,nv,neta,nq,npl,sigma).replace('.','d')
# array_save_directory = 'array_storage/batch_2/{}_nu_{}_nv_{}_neta_{}_nq_{}_npl_{}_sigma_{:.1E}/'.format(current_file_version,nu,nv,neta,nq,npl,sigma).replace('.','d')
if p.include_instrumental_effects:
	instrument_info = filter(None, p.instrument_model_directory.split('/'))[-1]
	array_save_directory = array_save_directory[:-1]+'_instrumental/'+instrument_info+'/'
	n_vis=p.n_vis
else:
	n_vis = 0
if npl==1:
	array_save_directory=array_save_directory.replace('_sigma', '_beta_{:.2E}_sigma'.format(p.beta))
if npl==2:
	array_save_directory=array_save_directory.replace('_sigma', '_b1_{:.2E}_b2_{:.2E}_sigma'.format(p.beta[0], p.beta[1]))

if p.fit_for_monopole:
	array_save_directory = array_save_directory[:-1]+'_fit_for_monopole_eq_True/'


#--------------------------------------------
# Construct matrices
#--------------------------------------------
BM = BuildMatrices(array_save_directory, nu, nv, nx, ny, n_vis, neta, nf, nq, sigma, npl=npl)
overwrite_existing_matrix_stack = False #Can be set to False unless npl>0
# overwrite_existing_matrix_stack = True #Can be set to False unless npl>0
proceed_without_overwrite_confirmation = False #Allows overwrite_existing_matrix_stack to be run without having to manually accept the deletion of the old matrix stack
BM.build_minimum_sufficient_matrix_stack(overwrite_existing_matrix_stack=overwrite_existing_matrix_stack, proceed_without_overwrite_confirmation=proceed_without_overwrite_confirmation)








# #--------------------------------------------
# # Generate GRN data. Currently only the bin selection component of this function is being used and should probably be spun out.
# #--------------------------------------------
# test_sim_out = generate_test_sim_signal_with_large_spectral_scales_2_21cmFAST_Binning(nu,nv,nx,ny,nf,neta,nq)
# if small_cube or True:
# 	s, s_im, s_LW_only, s_im_LW_only, s_fourier_only, s_im_fourier_only, bin_selector_in_k_cube_mask, high_spatial_frequency_selector_mask, k_cube_signal, k_sigma, ZM_mask, k_z_mean_mask = test_sim_out
# 	bin_selector_cube_ordered_list = bin_selector_in_k_cube_mask
# else:
# 	s=test_sim_out[0]
# 	bin_selector_cube_ordered_list = test_sim_out[6]
# 	high_spatial_frequency_selector_mask = test_sim_out[7]
# 	k_sigma = test_sim_out[9]
# 	ZM_mask = test_sim_out[10]
# 	k_z_mean_mask = test_sim_out[11]
# test_sim_out=0



# #--------------------------------------------
# # Define power spectral bins and coordinate cubes
# #--------------------------------------------
# if nq==0:
# 	map_bins_out = map_out_bins_for_power_spectral_coefficients_HERA_Binning(nu,nv,nx,ny,nf,neta,nq, bin_selector_cube_ordered_list,high_spatial_frequency_selector_mask, ZM_mask, k_z_mean_mask)
# 	bin_selector_in_model_mask_vis_ordered = map_bins_out
# 	bin_selector_vis_ordered_list = bin_selector_in_model_mask_vis_ordered
# else:
# 	map_bins_out = map_out_bins_for_power_spectral_coefficients_WQ_v2_HERA_Binning(nu,nv,nx,ny,nf,neta,nq, bin_selector_cube_ordered_list,high_spatial_frequency_selector_mask, ZM_mask, k_z_mean_mask)
# 	bin_selector_in_model_mask_vis_ordered_WQ, LW_modes_only_boolean_array_vis_ordered = map_bins_out
# 	bin_selector_vis_ordered_list = bin_selector_in_model_mask_vis_ordered_WQ
# map_bins_out=0







mod_k, k_x, k_y, k_z, deltakperp, deltakpara, x, y, z = generate_k_cube_in_physical_coordinates_21cmFAST_v2d0(nu,nv,nx,ny,nf,neta,p.box_size_21cmFAST_pix_sc,p.box_size_21cmFAST_Mpc_sc)
k=mod_k.copy()
k_vis_ordered = k.T.flatten()
# modk_vis_ordered_list = [k_vis_ordered[bin_selector.T.flatten()] for bin_selector in bin_selector_cube_ordered_list]

k_x_masked = generate_masked_coordinate_cubes(k_x, nu,nv,nx,ny,nf,neta,nq)
k_y_masked = generate_masked_coordinate_cubes(k_y, nu,nv,nx,ny,nf,neta,nq)
k_z_masked = generate_masked_coordinate_cubes(k_z, nu,nv,nx,ny,nf,neta,nq)
mod_k_masked = generate_masked_coordinate_cubes(mod_k, nu,nv,nx,ny,nf,neta,nq)

# k_cube_voxels_in_bin, modkbins_containing_voxels = generate_k_cube_model_spherical_binning(mod_k_masked, k_z_masked, nu,nv,nx,ny,nf,neta,nq)
# k_cube_voxels_in_bin, modkbins_containing_voxels = generate_k_cube_model_spherical_binning_v2d0(mod_k_masked, k_z_masked, nu,nv,nx,ny,nf,neta,nq)
k_cube_voxels_in_bin, modkbins_containing_voxels = generate_k_cube_model_spherical_binning_v2d1(mod_k_masked, k_z_masked, nu,nv,nx,ny,nf,neta,nq)

if p.use_uniform_prior_on_min_k_bin:
	print 'Excluding min-kz bin...'
	k_cube_voxels_in_bin = k_cube_voxels_in_bin[1:]
	modkbins_containing_voxels = modkbins_containing_voxels[1:]

modk_vis_ordered_list = [mod_k_masked[k_cube_voxels_in_bin[i_bin]] for i_bin in range(len(k_cube_voxels_in_bin))]
# k_vals_file_name = 'k_vals_nu_{}_nv_{}_nf_{}_nq_{}.txt'.format(nu,nv,nf,nq)
# k_vals_file_name = 'k_vals_nu_{}_nv_{}_nf_{}_nq_{}_binning v2d0.txt'.format(nu,nv,nf,nq)
# k_vals_file_name = 'k_vals_nu_{}_nv_{}_nf_{}_nq_{}_binning v2d1.txt'.format(nu,nv,nf,nq)
k_vals_file_name = 'k_vals_nu_{}_nv_{}_nf_{}_nq_{}_binning_v2d1.txt'.format(nu,nv,nf,nq)
k_vals = calc_mean_binned_k_vals(mod_k_masked, k_cube_voxels_in_bin, save_k_vals=True, k_vals_file=k_vals_file_name)

do_cylindrical_binning = False
if do_cylindrical_binning:
	n_k_perp_bins=2
	k_cube_voxels_in_bin, modkbins_containing_voxels, k_perp_bins = generate_k_cube_model_cylindrical_binning(mod_k_masked, k_z_masked, k_y_masked, k_x_masked, n_k_perp_bins, nu,nv,nx,ny,nf,neta,nq)





if not p.include_instrumental_effects:
	#--------------------------------------------
	# Generate mock-GDSE data
	#--------------------------------------------
	# p.use_GDSE_foreground_cube = False
	p.use_GDSE_foreground_cube = True
	use_GDSE_foreground_cube = p.use_GDSE_foreground_cube
	if use_GDSE_foreground_cube:
		###
		# GDSE foreground_outputs
		###	
		foreground_outputs = generate_Jelic_cube(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show, p.beta_experimental_mean,p.beta_experimental_std,p.gamma_mean,p.gamma_sigma,p.Tb_experimental_mean_K,p.Tb_experimental_std_K,p.nu_min_MHz,p.channel_width_MHz, generate_additional_extrapolated_HF_foreground_cube=True, fits_storage_dir=p.fits_storage_dir, HF_nu_min_MHz_array=p.HF_nu_min_MHz_array, simulation_FoV_deg=p.simulation_FoV_deg, simulation_resolution_deg=p.simulation_resolution_deg,random_seed=314211)

		fg_GDSE, s_GDSE, Tb_nu, beta_experimental_mean,beta_experimental_std,gamma_mean,gamma_sigma,Tb_experimental_mean_K,Tb_experimental_std_K,nu_min_MHz,channel_width_MHz, HF_Tb_nu = foreground_outputs
		foreground_outputs = []

		plot_figure = False
		if plot_figure:
			construct_aplpy_image_from_fits('/gpfs/data/jpober/psims/EoR/Python_Scripts/BayesEoR/git_version/BayesEoR/spec_model_tests/fits_storage/multi_frequency_band_pythonPStest1/Jelic_nu_min_MHz_159d0_TbStd_66d1866884116_beta_2d63_dbeta0d02/', 'Jelic_GDSE_cube_159MHz_mK', run_convert_from_mK_to_K=True, run_remove_unused_header_variables=True)

	#--------------------------------------------
	# Generate mock-free-free data
	#--------------------------------------------
	p.use_freefree_foreground_cube = False
	# p.use_freefree_foreground_cube = True
	use_freefree_foreground_cube = p.use_freefree_foreground_cube
	if use_freefree_foreground_cube:
		###
		# diffuse free-free foreground_outputs
		###	
		foreground_outputs_ff = generate_Jelic_cube(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show, p.beta_experimental_mean_ff,p.beta_experimental_std_ff,p.gamma_mean_ff,p.gamma_sigma_ff,p.Tb_experimental_mean_K_ff,p.Tb_experimental_std_K_ff,p.nu_min_MHz_ff,p.channel_width_MHz_ff, generate_additional_extrapolated_HF_foreground_cube=True, fits_storage_dir=p.fits_storage_dir_ff, HF_nu_min_MHz_array=p.HF_nu_min_MHz_array_ff, simulation_FoV_deg=p.simulation_FoV_deg_ff, simulation_resolution_deg=p.simulation_resolution_deg_ff,random_seed=3142111)

		fg_ff, s_ff = foreground_outputs_ff[:2]

		plot_figure = False
		if plot_figure:
			construct_aplpy_image_from_fits('/gpfs/data/jpober/psims/EoR/Python_Scripts/BayesEoR/git_version/BayesEoR/spec_model_tests/fits_storage/free_free_emission/Free_free_nu_min_MHz_159d0_TbStd_0d698184469839_beta_2d15_dbeta1e-10/', 'Jelic_GDSE_cube_159MHz_mK', run_convert_from_mK_to_K=True, run_remove_unused_header_variables=True)

	#--------------------------------------------
	# Load EGS data
	#--------------------------------------------
	p.use_EGS_cube = False
	# p.use_EGS_cube = True
	use_EGS_cube = p.use_EGS_cube
	if use_EGS_cube:
		print 'Using use_EGS_cube data'
		s_EGS, abc_EGS, scidata1_EGS = generate_data_from_loaded_EGS_cube(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show,p.EGS_npz_path)

	#--------------------------------------------
	# Load EoR data
	#--------------------------------------------
	# p.use_EoR_cube = True
	p.use_EoR_cube = False
	use_EoR_cube = p.use_EoR_cube
	if use_EoR_cube:
		print 'Using use_EoR_cube data'
		s_EoR, abc, scidata1 = generate_data_from_loaded_EoR_cube_v2d0(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show,chan_selection,p.EoR_npz_path_sc)



	calc_im_domain_noise = False
	if calc_im_domain_noise:
		sigma_complex = sigma/2**0.5
		noise_real = np.random.normal(0,sigma_complex,nu*nv*nf)
		noise_imag = np.random.normal(0,sigma_complex,nu*nv*nf)
		noise = noise_real+1j*noise_imag

		blank_cube = np.zeros([38,512,512])

		sci_f, sci_v, sci_u = blank_cube.shape
		sci_v_centre = sci_v/2
		sci_u_centre = sci_u/2
		blank_cube_subset = blank_cube[0:nf,sci_u_centre-nu/2:sci_u_centre+nu/2+1,sci_v_centre-nv/2:sci_v_centre+nv/2+1]
		blank_cube[0:nf,sci_u_centre-nu/2:sci_u_centre+nu/2+1,sci_v_centre-nv/2:sci_v_centre+nv/2+1] = noise.reshape(blank_cube_subset.shape) * blank_cube[0].size**0.5
		axes_tuple = (1,2)
		wnim=numpy.fft.ifftshift(blank_cube+0j, axes=axes_tuple)
		wnim=numpy.fft.ifftn(wnim, axes=axes_tuple) #FFT (python pre-normalises correctly! -- see parsevals theorem for discrete fourier transform.)
		wnim=numpy.fft.fftshift(wnim, axes=axes_tuple)

		print 'Image domain equivalent noise level:', wnim.std(), 'mK'
		print '21-cm simulation rms:', np.load('/users/psims/EoR/EoR_simulations/21cmFAST_512MPc_512pix_128pix/Fits/21cm_z10d2_mK.npz')['arr_0'].std(), 'mK'
		print '1/(S/N) level:', wnim.std() / np.load('/users/psims/EoR/EoR_simulations/21cmFAST_512MPc_512pix_128pix/Fits/21cm_z10d2_mK.npz')['arr_0'].std()



	calc_uv_domain_noise_in_Jy = False
	if calc_uv_domain_noise_in_Jy:
		sigma_complex = sigma/2**0.5
		noise_real = np.random.normal(0,sigma_complex,nu*nv*nf)
		noise_imag = np.random.normal(0,sigma_complex,nu*nv*nf)
		noise = noise_real+1j*noise_imag

		blank_cube = np.zeros([38,512,512])
		sci_f, sci_v, sci_u = blank_cube.shape
		sci_v_centre = sci_v/2
		sci_u_centre = sci_u/2
		blank_cube_subset = blank_cube[0:nf,sci_u_centre-nu/2:sci_u_centre+nu/2+1,sci_v_centre-nv/2:sci_v_centre+nv/2+1]
		blank_cube[0:nf,sci_u_centre-nu/2:sci_u_centre+nu/2+1,sci_v_centre-nv/2:sci_v_centre+nv/2+1] = noise.reshape(blank_cube_subset.shape) * blank_cube[0].size**0.5

		sigma_per_vis_non_standard_units = sigma
		da_sr = ((12./511)*np.pi/180.)**2.
		conversion_from_non_standard_units_to_mK_sr_units = da_sr*blank_cube[0].size**0.5
		mK_to_Jy_per_sr_conversion = (2*(p.nu_min_MHz*1.e6)**2*astropy.constants.k_B.value)/astropy.constants.c.value**2. /1.e-26

		sigma_per_vis_Jy = sigma_per_vis_non_standard_units*conversion_from_non_standard_units_to_mK_sr_units*mK_to_Jy_per_sr_conversion
		my_uv_points_to_HERA_uv_points_ratio = 960./666.
		HERA_equivalent_sigma_per_vis_Jy = sigma_per_vis_Jy/my_uv_points_to_HERA_uv_points_ratio
		print 'HERA_equivalent_sigma_per_vis_Jy:', HERA_equivalent_sigma_per_vis_Jy, 'Jy'



	#--------------------------------------------
	# Define data vector
	#--------------------------------------------
	non_instrmental_noise_seed = 42123
	if p.use_EoR_cube:
		print 'Using EoR cube'
		d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(sigma, s_EoR, nu,nv,nx,ny,nf,neta,nq, random_seed=non_instrmental_noise_seed)[0]
		s_Tot = s_EoR.copy()
		if p.use_GDSE_foreground_cube:
			print 'Using GDSE cube'
			d += generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(0.0, fg_GDSE, nu,nv,nx,ny,nf,neta,nq)[0]
			s_Tot += fg_GDSE
			s_fgs_only = fg_GDSE.copy()
		if p.use_freefree_foreground_cube:
			print 'Using free-free cube'
			d += generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(0.0, s_ff, nu,nv,nx,ny,nf,neta,nq)[0]
			s_Tot += s_ff
			s_fgs_only += s_ff
		if p.use_EGS_cube:
			print 'Using EGS cube'
			d += generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(0.0, s_EGS, nu,nv,nx,ny,nf,neta,nq)[0]
			s_Tot += s_EGS
			s_fgs_only += s_EGS
	elif p.use_GDSE_foreground_cube:
		d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(sigma, fg_GDSE, nu,nv,nx,ny,nf,neta,nq, random_seed=non_instrmental_noise_seed)[0]
		s_Tot = fg_GDSE.copy()
		s_fgs_only = fg_GDSE.copy()
		print 'Using GDSE cube'
		if p.use_freefree_foreground_cube:
			d += generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(0.0, s_ff, nu,nv,nx,ny,nf,neta,nq)[0]
			s_Tot += s_ff.copy()
			s_fgs_only += s_ff.copy()
			print 'Using free-free cube'
		if p.use_EGS_cube:
			d += generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(0.0, s_EGS, nu,nv,nx,ny,nf,neta,nq)[0]
			s_Tot += s_EGS.copy()
			s_fgs_only += s_EGS.copy()
			print 'Using EGS cube'
	elif p.use_EGS_cube:
		d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(sigma, s_EGS, nu,nv,nx,ny,nf,neta,nq, random_seed=non_instrmental_noise_seed)[0]
		s_Tot = s_EGS.copy()
		s_fgs_only = s_EGS.copy()
		print 'Using EGS cube'
	elif p.use_freefree_foreground_cube:
		d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(sigma, s_ff, nu,nv,nx,ny,nf,neta,nq, random_seed=non_instrmental_noise_seed)[0]
		s_Tot = s_ff.copy()
		s_fgs_only = s_ff.copy()
		print 'Using free-free cube'
	else:
		d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(sigma, s_EoR, nu,nv,nx,ny,nf,neta,nq, random_seed=non_instrmental_noise_seed)[0]
		s_Tot = s_EoR.copy()
		print 'Using EoR cube'


	effective_noise = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_v2(sigma, np.zeros(d.shape), nu,nv,nx,ny,nf,neta,nq, random_seed=non_instrmental_noise_seed)[1]
	effective_noise_std = effective_noise.std()




# if p.include_instrumental_effects:
# 	# np.random.seed(321)
# 	# d = np.random.normal(0,20,p.n_vis*p.nf)
# 	# np.random.seed(4321)
# 	# d = d+1j*np.random.normal(0,20,p.n_vis*p.nf)
# 	T = BM.read_data_from_hdf5(array_save_directory+'T.h5', 'T')
# 	s_WN, abc, scidata1 = generate_white_noise_signal(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z, T,Show,chan_selection,p.EoR_npz_path_sc)


T_Ninv_T = BM.read_data_from_hdf5(array_save_directory+'T_Ninv_T.h5', 'T_Ninv_T')
Npar = shape(T_Ninv_T)[0]

fit_for_LW_power_spectrum = True
# fit_for_LW_power_spectrum = False
masked_power_spectral_modes = np.ones(Npar)
if not fit_for_LW_power_spectrum:
	print 'Not fitting for LW power spectrum. Zeroing relevant modes in the determinant.'
	masked_power_spectral_modes[sorted(np.hstack(k_cube_voxels_in_bin)[0])] = 0.0

masked_power_spectral_modes = masked_power_spectral_modes.astype('bool')

T = BM.read_data_from_hdf5(array_save_directory+'T.h5', 'T')
Finv = BM.read_data_from_hdf5(array_save_directory+'Finv.h5', 'Finv')


overwrite_data_with_WN = False
if p.include_instrumental_effects:
	if overwrite_data_with_WN:
		# s_WN, abc, scidata1 = generate_white_noise_signal_instrumental_k_2_vis(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z, T,Show,chan_selection,masked_power_spectral_modes)
		s_WN, abc, scidata1 = generate_white_noise_signal_instrumental_im_2_vis(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z, Finv,Show,chan_selection,masked_power_spectral_modes, mod_k)
		d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(sigma, s_WN, nu,nv,nx,ny,nf,neta,nq,random_seed=2123)[0]
		effective_noise = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(sigma, s_WN, nu,nv,nx,ny,nf,neta,nq,random_seed=2123)[1]
	else:
		if p.use_EoR_cube:
			s_EoR, abc, scidata1 = generate_EoR_signal_instrumental_im_2_vis(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z, Finv,Show,chan_selection,masked_power_spectral_modes, mod_k, p.EoR_npz_path_sc)
			# EoR_noise_seed = 2123 #Used in v6
			# EoR_noise_seed = 42123 #Used in v5

			EoR_noise_seed = 742123

			# EoR_noise_seed = 1742123
			# EoR_noise_seed = 81742
			print 'EoR_noise_seed', EoR_noise_seed
			d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(1.0*sigma, s_EoR, nu,nv,nx,ny,nf,neta,nq,random_seed=EoR_noise_seed)[0]
			effective_noise = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(1.0*sigma, s_EoR, nu,nv,nx,ny,nf,neta,nq,random_seed=EoR_noise_seed)[1]

		use_foreground_cubes = True
		# use_foreground_cubes = False
		if use_foreground_cubes:
			p.use_GDSE_foreground_cube = True
			# p.use_GDSE_foreground_cube = False
			if p.use_GDSE_foreground_cube:
				# foreground_outputs = generate_Jelic_cube_instrumental_im_2_vis(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show, p.beta_experimental_mean,p.beta_experimental_std,p.gamma_mean,p.gamma_sigma,p.Tb_experimental_mean_K,p.Tb_experimental_std_K,p.nu_min_MHz,p.channel_width_MHz,Finv, generate_additional_extrapolated_HF_foreground_cube=True, fits_storage_dir=p.fits_storage_dir, HF_nu_min_MHz_array=p.HF_nu_min_MHz_array, simulation_FoV_deg=p.simulation_FoV_deg, simulation_resolution_deg=p.simulation_resolution_deg,random_seed=314211)

				p.beta_experimental_mean = 2.70
				# p.beta_experimental_mean = 2.0				
				# p.beta_experimental_std = 0.2
				# p.beta_experimental_mean = 2.63			
				p.beta_experimental_std = 1.e-10
				
				p.Tb_experimental_std_K = 1.e4


				foreground_outputs = generate_Jelic_cube_instrumental_im_2_vis_v2d0(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show, p.beta_experimental_mean,p.beta_experimental_std,p.gamma_mean,p.gamma_sigma,p.Tb_experimental_mean_K,p.Tb_experimental_std_K,p.nu_min_MHz,p.channel_width_MHz,Finv, generate_additional_extrapolated_HF_foreground_cube=True, fits_storage_dir=p.fits_storage_dir, HF_nu_min_MHz_array=p.HF_nu_min_MHz_array, simulation_FoV_deg=p.simulation_FoV_deg, simulation_resolution_deg=p.simulation_resolution_deg,random_seed=314211)


				fg_GDSE, s_GDSE, Tb_nu, beta_experimental_mean,beta_experimental_std,gamma_mean,gamma_sigma,Tb_experimental_mean_K,Tb_experimental_std_K,nu_min_MHz,channel_width_MHz, HF_Tb_nu, scidata1_subset = foreground_outputs
				foreground_outputs = []

				# scale_factor = (80./163.)**-2.7
				# scale_factor = (120./163.)**-2.7
				scale_factor = 1.0
				# noise_seed = 2123
				# noise_seed = 742123
				noise_seed = 42123
				# noise_seed = 1742123
				# noise_seed = 81742
				# d += generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(0.0, s_GDSE, nu,nv,nx,ny,nf,neta,nq,random_seed=noise_seed)[0]
				d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(sigma, s_GDSE*scale_factor, nu,nv,nx,ny,nf,neta,nq,random_seed=noise_seed)[0]
				effective_noise = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(sigma, s_GDSE, nu,nv,nx,ny,nf,neta,nq,random_seed=noise_seed)[1]

			# p.use_EGS_cube = True
			p.use_EGS_cube = False
			if p.use_EGS_cube:
				# foreground_outputs = generate_data_from_loaded_EGS_cube_im_2_vis(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show,p.EGS_npz_path,Finv)
				foreground_outputs = generate_data_from_loaded_EGS_cube_im_2_vis_v2d0(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show,p.EGS_npz_path,Finv)

				s_EGS, abc_EGS, scidata1_EGS = foreground_outputs
				foreground_outputs = []

				d += generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(0.0, s_EGS, nu,nv,nx,ny,nf,neta,nq,random_seed=noise_seed)[0]
				# d = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(sigma, s_EGS*1., nu,nv,nx,ny,nf,neta,nq,random_seed=2123)[0]
				effective_noise = generate_visibility_covariance_matrix_and_noise_realisation_and_the_data_vector_instrumental_v1(sigma, s_EGS, nu,nv,nx,ny,nf,neta,nq,random_seed=noise_seed)[1]





effective_noise_std = effective_noise.std()




# foreground_outputs = generate_Jelic_cube_instrumental_im_2_vis(nu,nv,nx,ny,nf,neta,nq,k_x, k_y, k_z,Show, p.beta_experimental_mean,1.e-10,p.gamma_mean,p.gamma_sigma,p.Tb_experimental_mean_K,p.Tb_experimental_std_K,p.nu_min_MHz,p.channel_width_MHz,Finv, generate_additional_extrapolated_HF_foreground_cube=True, fits_storage_dir=p.fits_storage_dir, HF_nu_min_MHz_array=p.HF_nu_min_MHz_array, simulation_FoV_deg=p.simulation_FoV_deg, simulation_resolution_deg=p.simulation_resolution_deg,random_seed=314211)

# beta_experimental_mean,beta_experimental_std,gamma_mean,gamma_sigma,Tb_experimental_mean_K,Tb_experimental_std_K,nu_min_MHz,channel_width_MHz = p.beta_experimental_mean,1.e-10,p.gamma_mean,p.gamma_sigma,p.Tb_experimental_mean_K,p.Tb_experimental_std_K,p.nu_min_MHz,p.channel_width_MHz

# generate_additional_extrapolated_HF_foreground_cube=True
# fits_storage_dir=p.fits_storage_dir
# HF_nu_min_MHz_array=p.HF_nu_min_MHz_array
# simulation_FoV_deg=p.simulation_FoV_deg
# simulation_resolution_deg=p.simulation_resolution_deg
# random_seed=314211



# calculte_PS_of_EoR_cube_directly = True
calculte_PS_of_EoR_cube_directly = False
if calculte_PS_of_EoR_cube_directly:
	#--------------------------------------------
	# Calculate power spectrum of the EoR subset cube and output it to file
	#--------------------------------------------
	# calculate_subset_cube_power_spectrum_v1d0(nu,nv,nx,ny,nf,neta,nq,k_cube_voxels_in_bin,modkbins_containing_voxels,p.EoR_npz_path_sc,mod_k,k_z)
	calculate_subset_cube_power_spectrum_v2d0(nu,nv,nx,ny,nf,neta,nq,k_cube_voxels_in_bin,modkbins_containing_voxels,p.EoR_npz_path_sc,mod_k,k_z)

	#--------------------------------------------
	# This function calculates both the power spectrum of the EoR subset cube and the (cylindrical) power spectrum of the full EoR cube in the k-space volume accessible to the subset cube in order to demonstrate that they are consistent within sample variance.
	# NOTE: while the power spectrum of the EoR subset cube is equal to the (cylindrical) power spectrum of the full EoR cube in the k-space volume accessible to the subset cube, it is not identical to the spherically averaged power specrum of the full EoR cube. This is due to the EoR cube output by 21cmFast not being spherically symmetric! (it is approximately sperically symmetric but only to within a factor of 2 in power). As mentioned above, this is solved by comparing the power spectra in matching regions of k-space (instead of comparing the small cylindrical subset of the spherical annulus to the full spherical annulus, which would only be expected to match for a truely spherically symmetric EoR power spectrum - i.e. no redshift space distortions etc.)!
	#--------------------------------------------
	calculate_21cmFAST_EoR_cube_power_spectrum_in_subset_cube_bins_v1d0(nu,nv,nx,ny,nf,neta,nq,k_cube_voxels_in_bin,modkbins_containing_voxels,p.EoR_npz_path_sc,mod_k,k_x,k_y,k_z)




#--------------------------------------------
# Load base matrices used in the likelihood and define related variables
#--------------------------------------------
T = BM.read_data_from_hdf5(array_save_directory+'T.h5', 'T')
T_Ninv_T = BM.read_data_from_hdf5(array_save_directory+'T_Ninv_T.h5', 'T_Ninv_T')
block_T_Ninv_T = BM.read_data_from_hdf5(array_save_directory+'block_T_Ninv_T.h5', 'block_T_Ninv_T')
Ninv = BM.read_data_from_hdf5(array_save_directory+'Ninv.h5', 'Ninv')
Ninv_d = np.dot(Ninv,d)
dbar = np.dot(T.conjugate().T,Ninv_d)
# Ninv=[]
Sigma_Diag_Indices=np.diag_indices(shape(T_Ninv_T)[0])
nDims = len(k_cube_voxels_in_bin)
d_Ninv_d = np.dot(d.conjugate(), Ninv_d)

if p.use_intrinsic_noise_fitting:
	nDims = nDims+1

###
# nDims = nDims+3 for Gaussian prior over the three long wavelength model vectors
###
if p.use_LWM_Gaussian_prior:
	nDims = nDims+3

x=[100.e0]*nDims
if p.fit_for_monopole:
	nuv = (nu*nv)
else:
	nuv = (nu*nv-1)
block_T_Ninv_T = np.array([np.hsplit(block,nuv) for block in np.vsplit(T_Ninv_T,nuv)])
if p.include_instrumental_effects:
	block_T_Ninv_T=[]


# multi_chan_P = BM.read_data_from_hdf5(array_save_directory+'multi_chan_P.h5', 'multi_chan_P')






# run_nudft_test=True
run_nudft_test=False
if run_nudft_test:
	###
	def Produce_Coordinate_Arrays_ZM(nu, nv, nx, ny):
		#U_oversampling_Factor=nu/float(nx) #Keeps uv-plane size constant and oversampled rather than DFTing to a larger uv-plane
		#V_oversampling_Factor=nv/float(ny) #Keeps uv-plane size constant and oversampled rather than DFTing to a larger uv-plane
		#
		i_y_Vector=(np.arange(ny)-ny/2)
		#i_y_Vector=numpy.fft.fftshift(arange(ny)) #This puts the centre of x,y grid: 0,0 at the centre of the vector rather than the start
		i_y_Vector=i_y_Vector.reshape(1,ny)
		i_y_Array=np.tile(i_y_Vector,ny)
		i_y_Array_Vectorised=i_y_Array.reshape(nx*ny,1)
		i_y_AV=i_y_Array_Vectorised
		#
		i_x_Vector=(np.arange(nx)-nx/2)
		#i_x_Vector=numpy.fft.fftshift(arange(nx)) #This puts the centre of x,y grid: 0,0 at the centre of the vector rather than the start
		i_x_Vector=i_x_Vector.reshape(nx,1)
		i_x_Array=np.tile(i_x_Vector,nx)
		i_x_Array_Vectorised=i_x_Array.reshape(nx*ny,1)
		i_x_AV=i_x_Array_Vectorised
		#
		i_v_Vector=(np.arange(nu)-nu/2)
		#i_v_Vector= numpy.fft.fftshift(arange(nu)) #This puts the centre of u,v grid: 0,0 at the centre of the vector rather than the start
		i_v_Vector=i_v_Vector.reshape(1,nu)
		i_v_Array=np.tile(i_v_Vector,nv)
		i_v_Array_Vectorised=i_v_Array.reshape(1,nu*nv)
		i_v_AV=i_v_Array_Vectorised
		i_v_AV=numpy.delete(i_v_AV,[i_v_AV.size/2]) #Remove the centre uv-pix
		#
		i_u_Vector=(np.arange(nv)-nv/2)
		#i_u_Vector=numpy.fft.fftshift(arange(nv)) #This puts the centre of u,v grid: 0,0 at the centre of the vector rather than the start
		i_u_Vector=i_u_Vector.reshape(nv,1)
		i_u_Array=np.tile(i_u_Vector,nu)
		i_u_Array_Vectorised=i_u_Array.reshape(1,nv*nu)
		i_u_AV=i_u_Array_Vectorised
		i_u_AV=numpy.delete(i_u_AV,[i_u_AV.size/2]) #Remove the centre uv-pix
		#
		#
		#ExponentArray=np.exp(-2.0*np.pi*1j*( (i_x_AV*i_u_AV/float(nx)) +  (i_v_AV*i_y_AV/float(ny)) ))
		return i_x_AV, i_y_AV, i_u_AV, i_v_AV



	nu, nv, nx, ny = p.nu, p.nv, p.nx, p.ny


	###
	def DFT_Array_DFT_2D_ZM(nu, nv, nx, ny):
		#
		i_x_AV, i_y_AV, i_u_AV, i_v_AV = Produce_Coordinate_Arrays_ZM(nu, nv, nx, ny)
		#
		ExponentArray=np.exp(-2.0*np.pi*1j*( (i_x_AV*i_u_AV/float(nx)) +  (i_v_AV*i_y_AV/float(ny)) ))
		return ExponentArray



	use_HERA_uv_coverage = True
	# use_HERA_uv_coverage = False
	if use_HERA_uv_coverage:
		i_x_AV, i_y_AV, i_u_AV, i_v_AV = Produce_Coordinate_Arrays_ZM(nu, nv, nx, ny)
		Jacob_uv_dict_dir = '/gpfs/data/jpober/shared/bayeseor_files/'
		uv_array = np.load(Jacob_uv_dict_dir+'noise_hera7-hex_1.0e+01rms_38nfreqs_5ntimes_phased.npy').item()
		i_u_AV = uv_array['uvw_array'][:,0]
		i_v_AV = uv_array['uvw_array'][:,1]

		# Check uv_array is Hermitian (everything should print true)
		for uv in uv_array['uvw_array'][:,:2]:                                 
		    if not (uv in uv_array['uvw_array'][:,:2] and -uv in uv_array['uvw_array'][:,:2]):
		    	print 'ERROR, uv_array is not Hermitian'


	else:
		i_x_AV, i_y_AV, i_u_AV, i_v_AV = Produce_Coordinate_Arrays_ZM(nu, nv, nx, ny)
		# i_u_AV = i_u_AV/2.
		# i_v_AV = i_v_AV/2.
		np.random.seed(123)
		i_u_AV_pt1 = np.random.uniform(i_u_AV.min(), i_u_AV.max(), len(i_u_AV)*3)
		i_u_AV = np.hstack((i_u_AV_pt1, -1.*i_u_AV_pt1[::-1]))
		np.random.seed(456)
		i_v_AV_pt1 = np.random.uniform(i_v_AV.min(), i_v_AV.max(), len(i_v_AV)*3)
		i_v_AV = np.hstack((i_v_AV_pt1, -1.*i_v_AV_pt1[::-1]))

	pylab.close('all')
	pylab.figure()
	pylab.scatter(i_u_AV, i_v_AV)
	pylab.show()


	dft_array = np.exp(-2.0*np.pi*1j*( (i_x_AV*i_u_AV/float(nx)) +  (i_v_AV*i_y_AV/float(ny)) ))





	# dft_array = BM.read_data_from_hdf5(array_save_directory+'dft_array.h5', 'dft_array')
	Finv = block_diag(*[dft_array.T for i in range(p.nf)])

	# Finv = BM.read_data_from_hdf5(array_save_directory+'Finv.h5', 'Finv')
	Fprime_Fz = BM.read_data_from_hdf5(array_save_directory+'Fprime_Fz.h5', 'Fprime_Fz')
	T = np.dot(Finv, Fprime_Fz)
	# Ninv = BM.read_data_from_hdf5(array_save_directory+'Ninv.h5', 'Ninv')
	Ninv = np.identity(T.shape[0])*1./sigma**2.	+0j
	Ninv_T = np.dot(Ninv,T)
	T_Ninv_T = np.dot(T.conjugate().T,Ninv_T)



	pylab.close('all')
	pylab.figure()
	pylab.imshow((dft_array.real))
	pylab.colorbar()
	pylab.show()


	pylab.close('all')
	pylab.figure()
	pylab.imshow((abs(Finv)))
	pylab.colorbar()
	pylab.show()


	pylab.close('all')
	pylab.figure()
	pylab.imshow(np.log10(abs(T)))
	pylab.colorbar()
	pylab.show()


	theta_test = np.zeros(T.shape[1])
	# theta_test[38*0+17] = 1.0
	for i in range(8):
		theta_test[38*i+17] = 1.0

	m_test = np.dot(T,theta_test)

	pylab.figure()
	pylab.imshow(abs(m_test.reshape(38,-1)))
	pylab.colorbar()
	pylab.show()


	pylab.figure()
	pylab.errorbar(arange(38), m_test.reshape(38,-1)[:,0].real)
	pylab.errorbar(arange(38), m_test.reshape(38,-1)[:,0].imag)
	# pylab.show()

	pylab.figure()
	pylab.errorbar(arange(38), abs(m_test.reshape(38,-1)[:,0]))
	pylab.show()


	Sigma = T_Ninv_T.copy()
	Sigma[np.diag_indices(len(T_Ninv_T))] += 1.e-10
	Sigma_inv = np.linalg.inv(Sigma)
	a = np.dot(Sigma_inv, Sigma)


	pylab.figure()
	pylab.imshow(abs(a))
	pylab.colorbar()
	pylab.figure()
	pylab.imshow(np.log10(abs(a)))
	pylab.colorbar()
	pylab.show()


	if p.useGPU:
		import pycuda.autoinit
		import pycuda.driver as cuda
		for devicenum in range(cuda.Device.count()):
		    device=cuda.Device(devicenum)
		    attrs=device.get_attributes()
		    print("\n===Attributes for device %d"%devicenum)
		    for (key,value) in attrs.iteritems():
		        print("%s:%s"%(str(key),str(value)))

		import time
		import numpy as np
		import ctypes
		from numpy import ctypeslib
		from scipy import linalg
		from subprocess import os

		current_dir = os.getcwd()
		base_dir = '/'.join(current_dir.split('/')[:np.where(np.array(current_dir.split('/'))=='BayesEoR')[0][-1]])+'/BayesEoR/'
		GPU_wrap_dir = base_dir+'likelihood_tests/SimpleEoRtestWQ/GPU_wrapper/'
		wrapmzpotrf=ctypes.CDLL(GPU_wrap_dir+'wrapmzpotrf.so')
		nrhs=1
		wrapmzpotrf.cpu_interface.argtypes = [ctypes.c_int, ctypes.c_int, ctypeslib.ndpointer(np.complex128, ndim=2, flags='C'), ctypeslib.ndpointer(np.complex128, ndim=1, flags='C'), ctypes.c_int]
		print 'Computing on GPU'

		print 'performing GPU inversion check...'
		dbar=np.ones_like(d)
		Sigma = T_Ninv_T.copy()
		# powers = 1.e-10
		powers = 10.
		Sigma[np.diag_indices(len(T_Ninv_T))] += powers

		dbar_copy = dbar.copy()
		dbar_copy_copy = dbar.copy()
		# wrapmzpotrf.cpu_interface(len(Sigma), nrhs, Sigma, dbar_copy, 1) #to print debug
		wrapmzpotrf.cpu_interface(len(Sigma), nrhs, Sigma, dbar_copy, 0)

		logdet_Magma_Sigma = np.sum(np.log(np.diag(abs(Sigma))))*2 #Note: After wrapmzpotrf, Sigma is actually SigmaCho (i.e. L with SigmaLL^T)
		SigmaI_dbar = linalg.cho_solve((Sigma.conjugate().T,True), dbar_copy_copy)

		Sigma = T_Ninv_T.copy()
		Sigma[np.diag_indices(len(T_Ninv_T))] += powers
		Sigma_SigmaI_dbar = np.dot(Sigma, SigmaI_dbar)

		returned_arrays_are_equal = np.allclose(dbar, Sigma_SigmaI_dbar, rtol=sigma/1.e3)
		if returned_arrays_are_equal:
			print 'Sigma inversion worked correctly'
		else:
			print 'A problem occured with the inversion of Sigma.....'





T[:,19::40].imag = 0.0
T[:,38::40].imag = 0.0
T[:,39::40].imag = 0.0

T_Ninv_T = np.dot(T.conjugate().T,np.dot(Ninv,T))
dbar = np.dot(T.conjugate().T,Ninv_d)




sub_MLLWM = True


# if nq==0:
# 	masked_power_spectral_modes = np.logical_not(np.logical_or.reduce(bin_selector_in_model_mask_vis_ordered).reshape(-1,neta)).flatten()
# else:
# 	masked_power_spectral_modes = LW_modes_only_boolean_array_vis_ordered
from numpy import real

#--------------------------------------------
# Instantiate class and check that posterior_probability returns a finite probability (so no obvious binning errors etc.)
#--------------------------------------------
if small_cube: PSPP = PowerSpectrumPosteriorProbability(T_Ninv_T, dbar, Sigma_Diag_Indices, Npar, k_cube_voxels_in_bin, nuv, nu, nv, nx, ny, neta, nf, nq, masked_power_spectral_modes, modk_vis_ordered_list, Ninv, d_Ninv_d, log_priors=False, intrinsic_noise_fitting=p.use_intrinsic_noise_fitting)
PSPP_block_diag = PowerSpectrumPosteriorProbability(T_Ninv_T, dbar, Sigma_Diag_Indices, Npar, k_cube_voxels_in_bin, nuv, nu, nv, nx, ny, neta, nf, nq, masked_power_spectral_modes, modk_vis_ordered_list, Ninv, d_Ninv_d, block_T_Ninv_T=block_T_Ninv_T, Print=True, log_priors=False, intrinsic_noise_fitting=p.use_intrinsic_noise_fitting)
self = PowerSpectrumPosteriorProbability(T_Ninv_T, dbar, Sigma_Diag_Indices, Npar, k_cube_voxels_in_bin, nuv, nu, nv, nx, ny, neta, nf, nq, masked_power_spectral_modes, modk_vis_ordered_list, Ninv, d_Ninv_d, block_T_Ninv_T=block_T_Ninv_T, Print=True, log_priors=False, intrinsic_noise_fitting=p.use_intrinsic_noise_fitting)
start = time.time()

if small_cube:
	# print PSPP.posterior_probability([1.e0]*nDims, diagonal_sigma=False)[0]
	print PSPP_block_diag.posterior_probability([1.e0]*nDims, diagonal_sigma=False, block_T_Ninv_T=block_T_Ninv_T)[0]


iterative_sub_MLLWM = True #Fit iteratively to sidestep numerical limitations (complex double precision) of the inversion
# iterative_sub_MLLWM = False #Fit iteratively to sidestep numerical limitations (complex double precision) of the inversion
if sub_MLLWM:
	if not iterative_sub_MLLWM:
		pre_sub_dbar = PSPP_block_diag.dbar
		PSPP_block_diag.dimensionless_PS=True
		PSPP_block_diag.inverse_LW_power=p.inverse_LW_power #Include minimal prior over LW modes to ensure numerical stability
		if p.use_LWM_Gaussian_prior:
			fit_constraints = [9.e9,9.e9,9.e9]+[1.e-20]*(nDims-3)
		else:
			PSPP_block_diag.inverse_LW_power = 1.e-20
			fit_constraints = [1.e-20]*(nDims)
		maxL_LW_fit = PSPP_block_diag.calc_SigmaI_dbar_wrapper(fit_constraints, T_Ninv_T, pre_sub_dbar, block_T_Ninv_T=block_T_Ninv_T)[0]
		maxL_LW_signal = np.dot(T,maxL_LW_fit)
		Ninv = BM.read_data_from_hdf5(array_save_directory+'Ninv.h5', 'Ninv')
		Ninv_maxL_LW_signal = np.dot(Ninv,maxL_LW_signal)
		ML_qbar = np.dot(T.conjugate().T,Ninv_maxL_LW_signal)
		q_sub_dbar = pre_sub_dbar-ML_qbar
		if small_cube: PSPP.dbar = q_sub_dbar
		PSPP_block_diag.dbar = q_sub_dbar
		print '(d - s_GDSE).std()', effective_noise_std
		print '(d - maxL_LW_signal).std()', (d - maxL_LW_signal).std()
		PSPP_block_diag.inverse_LW_power = p.inverse_LW_power #Reset inverse_LW_power to ensure numerical stability with non-zero Fourier modes

		if small_cube:
			print PSPP.posterior_probability([1.e0]*nDims, diagonal_sigma=False)[0]
			print PSPP_block_diag.posterior_probability([1.e0]*nDims, diagonal_sigma=False, block_T_Ninv_T=block_T_Ninv_T)[0]
		if p.use_intrinsic_noise_fitting:
			q_sub_d = d - maxL_LW_signal
			Ninv_q_sub_d = np.dot(Ninv, q_sub_d)
			q_sub_d_Ninv_q_sub_d = np.dot(q_sub_d, Ninv_q_sub_d)
			PSPP_block_diag.d_Ninv_d = 	q_sub_d_Ninv_q_sub_d


	else:
		Ninv = BM.read_data_from_hdf5(array_save_directory+'Ninv.h5', 'Ninv')
		maxL_LW_fit_array = []
		maxL_LW_signal_array = []
		pre_sub_dbar = PSPP_block_diag.dbar
		PSPP_block_diag.dimensionless_PS=True
		PSPP_block_diag.inverse_LW_power=p.inverse_LW_power #Include minimal prior over LW modes to ensure numerical stability
		dbar_prime_i = dbar.copy()
		d_prime_i = d.copy()

		PSPP_block_diag.Print = True
		print 'effective_noise_std', effective_noise_std

		count=0
		# count_max = 10
		count_max = 0
		maxL_LW_signal = np.zeros(len(d))
		bias_threshold = 0.0
		# bias_threshold = -1.0

		# for i in range(7):
		while count<=count_max and d_prime_i.std() >= (1.0+bias_threshold)*effective_noise_std:
			# fit_constraints = [9.e9,9.e9,9.e9]+[1.e-20]*(nDims-3)
			# fit_constraints = [1.e9,1.e9,1.e9]+[1.e-20]*(nDims-3)
			if p.use_LWM_Gaussian_prior:
				fit_constraints = [1.e9,1.e9,1.e9]+[1.e-20]*(nDims-3)
			else:
				# PSPP_block_diag.inverse_LW_power = 8.e-21 #2000
				# PSPP_block_diag.inverse_LW_power = 2e-21 #4000
				PSPP_block_diag.inverse_LW_power = 2e-18
				if p.beta==[-1.0,-2.0]:
					# PSPP_block_diag.inverse_LW_power = 2.e-21 #2000 (rather than 2e-18; quadratic can invert when closer to uniform while remaining stable)
					PSPP_block_diag.inverse_LW_power = 2e-20 #2000 (rather than 2e-18; quadratic can invert when closer to uniform while remaining stable)
				print 'PSPP_block_diag.inverse_LW_power:', PSPP_block_diag.inverse_LW_power
				#
				# PSPP_block_diag.inverse_LW_power = 0.0
				# PSPP_block_diag.inverse_LW_power_zeroth_LW_term = 2e-20
				# PSPP_block_diag.inverse_LW_power_first_LW_term = 2e-20
				# PSPP_block_diag.inverse_LW_power_second_LW_term = 2.e20
				# if count==count_max:
				# 	print 'count_max param update'
				# 	PSPP_block_diag.inverse_LW_power = 2e-21 #4000

				fit_constraints = [1.e-100]*(nDims)

			maxL_LW_fit = PSPP_block_diag.calc_SigmaI_dbar_wrapper(fit_constraints, T_Ninv_T, dbar_prime_i, block_T_Ninv_T=block_T_Ninv_T)[0]
			maxL_LW_signal = np.dot(T,maxL_LW_fit)

			maxL_LW_fit_array.append(maxL_LW_fit)
			maxL_LW_signal_array.append(maxL_LW_signal)

			print count, (d_prime_i - maxL_LW_signal).std(), '\n'

			d_prime_i = (d_prime_i - maxL_LW_signal)
			Ninv_d_prime_i = np.dot(Ninv,d_prime_i)
			dbar_prime_i = np.dot(T.conjugate().T,Ninv_d_prime_i)
			count+=1


		maxL_LW_fit_array = np.array(maxL_LW_fit_array)
		maxL_LW_signal_array = np.array(maxL_LW_signal_array)

		total_maxL_LW_fit = np.sum(maxL_LW_fit_array, axis=0)
		total_maxL_LW_signal = np.dot(T,total_maxL_LW_fit)

		Ninv_total_maxL_LW_signal = np.dot(Ninv,total_maxL_LW_signal)
		ML_qbar = np.dot(T.conjugate().T,Ninv_total_maxL_LW_signal)
		q_sub_dbar = pre_sub_dbar-ML_qbar
		if small_cube: PSPP.dbar = q_sub_dbar
		PSPP_block_diag.dbar = q_sub_dbar
		PSPP_block_diag.inverse_LW_power = p.inverse_LW_power #Reset inverse_LW_power to ensure numerical stability with non-zero Fourier modes

		print 'Iterative foreground pre-subtraction complete, {} orders of magnitude foreground supression achieved.\n'.format(np.log10((d-effective_noise).std()/(d-total_maxL_LW_signal-effective_noise).std()))

		if small_cube:
			print PSPP.posterior_probability([1.e0]*nDims, diagonal_sigma=False)[0]
			print PSPP_block_diag.posterior_probability([1.e0]*nDims, diagonal_sigma=False, block_T_Ninv_T=block_T_Ninv_T)[0]

		if p.use_intrinsic_noise_fitting:
			q_sub_d = d - total_maxL_LW_signal
			Ninv_q_sub_d = np.dot(Ninv, q_sub_d)
			q_sub_d_Ninv_q_sub_d = np.dot(q_sub_d, Ninv_q_sub_d)
			PSPP_block_diag.d_Ninv_d = 	q_sub_d_Ninv_q_sub_d






Q_T = np.array([row for i,row in enumerate(T.T) if (i+((neta+nq)-neta+0))%(neta+nq)==0 or (i+((neta+nq)-neta/2))%(neta+nq)==0 or (i+((neta+nq)-neta-1))%(neta+nq)==0]).T

Q_maxL_LW_fit = np.array([row for i,row in enumerate(maxL_LW_fit) if (i+((neta+nq)-neta+0))%(neta+nq)==0 or (i+((neta+nq)-neta/2))%(neta+nq)==0 or (i+((neta+nq)-neta-1))%(neta+nq)==0])

Q_T.imag=0.0

Q_T_Ninv_Q_T = np.dot(Q_T.conjugate().T, np.dot(Ninv, Q_T))
Ninv_d = np.dot(Ninv,d)
Qdbar = np.dot(Q_T.conjugate().T,Ninv_d)

a_hat = np.linalg.solve(Q_T_Ninv_Q_T, Qdbar)



print 'Iterative foreground pre-subtraction complete, {} orders of magnitude foreground supression achieved.\n'.format(np.log10((d-effective_noise).std()/(d-np.dot(T, maxL_LW_fit)-effective_noise).std()))

print 'Iterative foreground pre-subtraction2 complete, {} orders of magnitude foreground supression achieved.\n'.format(np.log10((d-effective_noise).std()/(d-np.dot(Q_T, a_hat)-effective_noise).std()))





do_null_space_test = False
if do_null_space_test:
	a = np.linalg.svd(Finv)
	U = a[0]
	U1 = U[:,0:Finv.shape[1]]

	test_im = np.random.normal(0.0,1,Finv.shape[1])
	test_vis = np.dot(Finv, np.random.normal(test_im))
	test_sigma = 1.e-5
	test_n = np.random.normal(0.0,test_sigma,Finv.shape[0])+1j*np.random.normal(0.0,test_sigma,Finv.shape[0])
	test_vis = test_vis+test_n
	test_Ninv = np.identity(Finv.shape[0])/test_sigma**2.

	U1_test_Ninv_U1 = np.dot(U1.conjugate().T, np.dot(test_Ninv,U1))
	U1_test_Ninv_U1_inv = np.linalg.inv(U1_test_Ninv_U1)
	U1_test_Ninv_d = np.dot(U1.conjugate().T, np.dot(test_Ninv,test_vis))

	test_a = np.dot(U1_test_Ninv_U1_inv, U1_test_Ninv_d)
	model_vis = np.dot(U1,test_a)

	a1 = np.dot(a[0][:, :(len(a[1]))]*a[1], a[2])
	print 'a1 == Finv?:', np.allclose(Finv, a1)
	print abs(Finv-a1).max()

	print np.sum((a[1]**2.))
	print np.sum((a[1]**2.))*0.9
	print np.sum((a[1]**2.)[0:520]) #Exclude highest weighted vectors (the highest weighted that sum to 90% of the weight)

	###

	singular_values_with_greater_than_10pow5_downweighting = np.where(a[1]<1.e-2)
	# singular_values_with_greater_than_10pow5_downweighting = np.where(a[1][520:])
	null_space_im_vectors = a[2][:,singular_values_with_greater_than_10pow5_downweighting[0]]
	ns1 = null_space_im_vectors.copy()

	ns1 = np.hstack((pl1,null_space_im_vectors))
	# ns1 = pl1.copy()

	d_im = scidata1_subset.copy()
	# if not p.fit_for_monopole:
	for i_chan in range(len(d_im)):
		d_im[i_chan] = d_im[i_chan]-d_im[i_chan].mean()
	d_im = d_im.flatten()

	sigma_im = 1.e-10
	noise = np.random.normal(0,sigma_im,d_im.size)
	d_im = d_im+noise
	N_im_inv = np.identity(d_im.size)/sigma_im**2.

	ns1_N_im_inv_ns1 = np.dot(ns1.conjugate().T, np.dot(N_im_inv, ns1))
	ns1_N_im_inv_ns1_inv = np.linalg.inv(ns1_N_im_inv_ns1)
	print np.sum(abs(np.dot(ns1_N_im_inv_ns1_inv,ns1_N_im_inv_ns1) -1.0)<1.e-10)

	ns1_N_im_inv_d_im = np.dot(ns1.conjugate().T, np.dot(N_im_inv, d_im))

	ml_theta = np.dot(ns1_N_im_inv_ns1_inv,ns1_N_im_inv_d_im)
	ml_null_im = np.dot(ns1,ml_theta)

	print (d_im-ml_null_im).max()
	print (d_im-ml_null_im).std()
	print np.log10((d_im-ml_null_im).std()/d_im.std())




# -----------------------------------------------
# -----------------------------------------------
###
# ML image model recovery testing
###
ML_image_model_recovery_testing = True
# ML_image_model_recovery_testing = False
if ML_image_model_recovery_testing:

	Fprime_Fz = BM.read_data_from_hdf5(array_save_directory+'Fprime_Fz.h5', 'Fprime_Fz')

	###
	# Single power law fit
	###
	# pl1 = Fprime_Fz.T[19::neta+nq].T.copy()
	pl1 = Fprime_Fz.T[neta/2::neta+nq].T.copy()
	# d_im = Tb_nu[:,0:9,0:9].copy()
	d_im = scidata1_subset.copy()
	# if not p.fit_for_monopole:
	for i_chan in range(len(d_im)):
		d_im[i_chan] = d_im[i_chan]-d_im[i_chan].mean()
	d_im = d_im.flatten()

	sigma_im = 1.e-10
	noise = np.random.normal(0,sigma_im,d_im.size)
	d_im = d_im+noise
	N_im_inv = np.identity(d_im.size)/sigma_im**2.

	pl1_N_im_inv_pl1 = np.dot(pl1.conjugate().T, np.dot(N_im_inv, pl1))
	pl1_N_im_inv_pl1_inv = np.linalg.inv(pl1_N_im_inv_pl1)
	print np.sum(abs(np.dot(pl1_N_im_inv_pl1_inv,pl1_N_im_inv_pl1) -1.0)<1.e-10)

	# pl1_N_im_inv_d_im = np.dot(pl1.conjugate().T, np.dot(N_im_inv, d_im))
	pl1_N_im_inv_d_im = np.dot(pl1.conjugate().T, np.dot(N_im_inv, d_im))

	ml_theta = np.dot(pl1_N_im_inv_pl1_inv,pl1_N_im_inv_d_im)
	ml_im = np.dot(pl1,ml_theta)

	print (d_im-ml_im).max()
	print (d_im-ml_im).std()
	print np.log10((d_im-ml_im).std()/d_im.std())
	# print np.log10((d_im-ml_im-	ml_null_im).std()/d_im.std())

	###
	# Constant plus single power law fit
	###
	# cpl1 = np.array([row for i,row in enumerate(Fprime_Fz.T) if (i+((neta+nq)-38))%(neta+nq)==0 or (i+((neta+nq)-19))%(neta+nq)==0]).T
	cpl1 = np.array([row for i,row in enumerate(Fprime_Fz.T) if (i+((neta+nq)-neta+0))%(neta+nq)==0 or (i+((neta+nq)-neta/2))%(neta+nq)==0]).T

	# d_im = Tb_nu[:,0:9,0:9].copy()
	d_im = scidata1_subset.copy()
	for i_chan in range(len(d_im)):
		d_im[i_chan] = d_im[i_chan]-d_im[i_chan].mean()
	d_im = d_im.flatten()

	sigma_im = 1.e-10
	noise = np.random.normal(0,sigma_im,d_im.size)
	d_im = d_im+noise
	N_im_inv = np.identity(d_im.size)/sigma_im**2.

	cpl1_N_im_inv_cpl1 = np.dot(cpl1.conjugate().T, np.dot(N_im_inv, cpl1))
	cpl1_N_im_inv_cpl1_inv = np.linalg.inv(cpl1_N_im_inv_cpl1)
	print np.sum(abs(np.dot(cpl1_N_im_inv_cpl1_inv,cpl1_N_im_inv_cpl1) -1.0)<1.e-10)

	cpl1_N_im_inv_d_im = np.dot(cpl1.conjugate().T, np.dot(N_im_inv, d_im))

	ml_theta = np.dot(cpl1_N_im_inv_cpl1_inv,cpl1_N_im_inv_d_im)
	ml_im = np.dot(cpl1,ml_theta)

	print (d_im-ml_im).max()
	print (d_im-ml_im).std()
	print np.log10((d_im-ml_im).std()/d_im.std())

# -----------------------------------------------
# -----------------------------------------------











# -----------------------------------------------
###
# NOTE: this cross-check is not exactly in the right place in the code because it requires running sub_MLLWM (below) to derive maxL_LW_fit as well as ML_image_model_recovery_testing (above) to derive d_im first!
###
ml_theta_vis_im = np.dot(Fprime_Fz,maxL_LW_fit)
np.log10((d_im-ml_theta_vis_im).std()/d_im.std())
np.log10((np.dot(Finv,d_im)-np.dot(Finv,ml_theta_vis_im)).std()/(np.dot(Finv,d_im).std()))
np.log10((np.dot(Finv,d_im)-np.dot(Finv,ml_theta_vis_im.real)).std()/(np.dot(Finv,d_im).std()))
np.log10((np.dot(Finv,(d_im-ml_theta_vis_im))).std()/(np.dot(Finv,d_im).std()))



base_dir = 'Plots'
# save_dir = base_dir+'/image_vs_visibility_space_fitting/{}/'.format(filter(None,array_save_directory.split('/'))[-1])
save_dir = base_dir+'/image_vs_visibility_space_fitting/{}/'.format('/'.join(filter(None, array_save_directory.split('/'))[2:]))
if not os.path.isdir(save_dir):
		os.makedirs(save_dir)





savefig = True
# savefig = False
pylab.close('all')
im_normalisation = abs(d_im).mean()
vis_normalisation = abs(np.dot(Finv,d_im)).mean()
fig, ax = pylab.subplots(nrows=6, ncols=3, figsize = (10,20))
ax[0,0].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),d_im.reshape(38,-1).real/im_normalisation)
ax[0,1].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),ml_im.reshape(38,-1).real/im_normalisation)
ax[0,2].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),((d_im-ml_im)).real.reshape(38,-1)/im_normalisation)
ax[1,0].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,d_im).real.reshape(38,-1)/vis_normalisation)
ax[1,1].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,ml_im).real.reshape(38,-1)/vis_normalisation)
ax[1,2].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,(d_im-ml_im)).real.reshape(38,-1)/vis_normalisation)
ax[2,0].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,d_im).imag.reshape(38,-1)/vis_normalisation)
ax[2,1].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,ml_im).imag.reshape(38,-1)/vis_normalisation)
ax[2,2].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,(d_im-ml_im)).imag.reshape(38,-1)/vis_normalisation)
ax[3,0].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),d_im.reshape(38,-1).real/im_normalisation)
ax[3,1].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),ml_theta_vis_im.reshape(38,-1).real/im_normalisation)
ax[3,2].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),((d_im-ml_theta_vis_im)).reshape(38,-1).real/im_normalisation)
ax[4,0].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,d_im).real.reshape(38,-1)/vis_normalisation)
ax[4,1].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,ml_theta_vis_im).real.reshape(38,-1)/vis_normalisation)
ax[4,2].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,(d_im-ml_theta_vis_im)).real.reshape(38,-1)/vis_normalisation)
ax[5,0].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,d_im).imag.reshape(38,-1)/vis_normalisation)
ax[5,1].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,ml_theta_vis_im).imag.reshape(38,-1)/vis_normalisation)
ax[5,2].plot((p.nu_min_MHz+np.arange(38)*p.channel_width_MHz),np.dot(Finv,(d_im-ml_theta_vis_im)).imag.reshape(38,-1)/vis_normalisation)
for ax_ in ax.ravel():
	ax_.set_xlabel('$\\nu$')
	ax_.set_ylabel('Amplitude')
fig.tight_layout()

if savefig: fig.savefig(save_dir+'spectra_and_spectral_residuals_from_image_vs_visibility_space_fitting_v1d0.png')
fig.show()



pylab.close('all')
im_normalisation = abs(d_im).mean()
fig, ax = pylab.subplots(nrows=2, ncols=2, figsize = (10,10))
a00 = ax[0,0].imshow(((d_im-ml_theta_vis_im)).reshape(38,-1).T.real/im_normalisation)
fig.colorbar(a00, ax=ax[0,0])
a01 = ax[0,1].imshow(((d_im-ml_theta_vis_im)).reshape(38,-1)[0].reshape(9,9).real/im_normalisation)
fig.colorbar(a01, ax=ax[0,1])
a10 = ax[1,0].imshow(((d_im-ml_im)).reshape(38,-1).T.real/im_normalisation)
fig.colorbar(a10, ax=ax[1,0])
a11 = ax[1,1].imshow(((d_im-ml_im)).reshape(38,-1)[0].reshape(9,9).real/im_normalisation)
fig.colorbar(a11, ax=ax[1,1])
fig.tight_layout()
if savefig: fig.savefig(save_dir+'image_residuals_from_image_vs_visibility_space_fitting_v1d0.png')
fig.show()
# -----------------------------------------------








